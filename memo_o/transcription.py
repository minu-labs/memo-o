import logging
import queue
import threading
import time

from PySide6.QtCore import QObject, Signal

from . import db as dbm
from .db import Database
from .i18n import tr
from .stt import DEFAULT_MODEL, DEFAULT_SPEECH_LANG, Transcriber, TranscriptionCancelled
from .wavfile import repair

log = logging.getLogger(__name__)
MIN_DURATION = 0.5  # 이보다 짧은 녹음은 변환하지 않는다 (실수로 두 번 누른 경우 등)


class TranscriptionService(QObject):
    """녹음이 끝나면 순서대로 백그라운드에서 텍스트로 변환한다."""

    changed = Signal(int)            # 상태가 바뀐 녹음 id
    progress = Signal(int, float)    # (id, 0~1)

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self._queue: queue.Queue[int | None] = queue.Queue()
        self._transcriber = Transcriber()
        self._progress: dict[int, float] = {}
        self._current: int | None = None
        self._cancel_ids: set[int] = set()
        self._shutdown = False
        self._thread = threading.Thread(target=self._run, name="memoo-stt", daemon=True)

    @property
    def device(self) -> str:
        return self._transcriber.device

    def start(self) -> None:
        self.recover()
        for rid in self.db.ids_with_status(dbm.PENDING, dbm.TRANSCRIBING):
            self.db.update(rid, status=dbm.PENDING)
            self._queue.put(rid)
        self._thread.start()

    def recover(self) -> None:
        """강제 종료로 '녹음 중'에 머문 항목의 WAV 헤더를 복구해 변환 대기로 돌린다."""
        for rid in self.db.ids_with_status(dbm.RECORDING):
            rec = self.db.get(rid)
            try:
                duration = repair(rec.file_path)
                self.db.update(rid, duration=duration, status=dbm.PENDING)
                log.info("녹음 복구: %s (%.1fs)", rec.file_path, duration)
            except Exception as e:
                log.exception("녹음 복구 실패: %s", rec.file_path)
                self.db.update(rid, status=dbm.ERROR, error=tr("stt.recover_failed", e=e))

    def enqueue(self, rec_id: int) -> None:
        self._cancel_ids.discard(rec_id)
        self.db.update(rec_id, status=dbm.PENDING, error=None)
        self._queue.put(rec_id)
        self.changed.emit(rec_id)

    def cancel(self, rec_id: int) -> None:
        self._cancel_ids.add(rec_id)

    def progress_of(self, rec_id: int) -> float | None:
        return self._progress.get(rec_id)

    def shutdown(self, timeout: float = 3.0) -> None:
        self._shutdown = True
        self._queue.put(None)
        self._thread.join(timeout)

    def _run(self) -> None:
        try:
            self._transcriber.warmup(self.db.get_setting("model", DEFAULT_MODEL))
        except Exception:
            log.exception("모델 사전 로드 실패 (첫 변환 시 다시 시도됩니다)")
        while True:
            rid = self._queue.get()
            if rid is None or self._shutdown:
                break
            if rid in self._cancel_ids:
                continue
            rec = self.db.get(rid)
            if rec is None or rec.status != dbm.PENDING:
                continue
            self._transcribe(rec)
        self.db.close()

    def _transcribe(self, rec: dbm.Recording) -> None:
        rid = rec.id
        size = self.db.get_setting("model", DEFAULT_MODEL)
        lang = self.db.get_setting("stt_lang", DEFAULT_SPEECH_LANG)
        self._current = rid
        self._progress[rid] = 0.0
        self.db.update(rid, status=dbm.TRANSCRIBING)
        self.changed.emit(rid)
        last_emit = 0.0

        def on_progress(p: float) -> None:
            nonlocal last_emit
            p = max(p, self._progress.get(rid, 0.0))
            self._progress[rid] = p
            now = time.monotonic()
            if now - last_emit > 0.3 or p >= 1.0:
                last_emit = now
                self.progress.emit(rid, p)

        def cancelled() -> bool:
            return self._shutdown or rid in self._cancel_ids

        # faster-whisper는 감지된 '말 구간'이 끝나야 진행률을 알려준다. 끊김 없이 이어지는
        # 짧은 녹음은 구간이 하나뿐이라 완료 직전까지 콜백이 안 와, 경과 시간 기반으로
        # 추정치를 채워 넣어 화면이 0%에 멈춰 보이지 않게 한다 (실제 콜백이 오면 그 값 우선).
        started = time.monotonic()
        stop_estimate = threading.Event()

        def _estimate() -> None:
            if rec.duration <= 0:
                return
            while not stop_estimate.wait(0.3):
                on_progress(min((time.monotonic() - started) / rec.duration, 0.95))

        estimator = threading.Thread(target=_estimate, name="memoo-stt-progress", daemon=True)
        estimator.start()
        try:
            if not rec.file_path.exists():
                raise FileNotFoundError(tr("stt.file_missing"))
            if rec.duration < MIN_DURATION:
                segments = []
            else:
                segments = self._transcriber.transcribe(rec.file_path, size, lang, on_progress, cancelled)
            if self.db.get(rid) is not None:
                self.db.save_transcript(rid, segments, size)
        except TranscriptionCancelled:
            if self.db.get(rid) is not None:
                self.db.update(rid, status=dbm.PENDING)
        except Exception as e:
            log.exception("변환 실패: %s", rec.file_path)
            if self.db.get(rid) is not None:
                self.db.update(rid, status=dbm.ERROR, error=str(e))
        finally:
            stop_estimate.set()
            estimator.join(timeout=1)
            self._current = None
            self._progress.pop(rid, None)
            self.changed.emit(rid)
