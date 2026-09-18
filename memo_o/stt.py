import logging
import os
from collections.abc import Callable
from pathlib import Path

from .db import Segment
from .paths import model_search_dirs

log = logging.getLogger(__name__)

MODEL_SIZES = ("small", "medium")
DEFAULT_MODEL = "small"


class TranscriptionCancelled(Exception):
    pass


def find_model(size: str) -> Path | None:
    for base in model_search_dirs():
        d = base / size
        if (d / "model.bin").is_file():
            return d
    return None


def available_models() -> dict[str, Path]:
    return {s: p for s in MODEL_SIZES if (p := find_model(s))}


def _cuda_available() -> bool:
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


class Transcriber:
    """모델은 한 번 로드해 재사용. 네트워크 접근 없이 로컬 폴더에서만 로드한다."""

    def __init__(self):
        self._model = None
        self._model_key: tuple[str, str] | None = None
        self.device = "cpu"

    def _load(self, size: str):
        path = find_model(size)
        if path is None:
            raise FileNotFoundError(
                f"'{size}' 모델을 찾을 수 없습니다. 설치 폴더 또는 데이터 폴더의 models\\{size} 에 모델 파일을 넣어주세요."
            )
        key = (size, str(path))
        if self._model is not None and self._model_key == key:
            return self._model

        from faster_whisper import WhisperModel

        self._model = None
        if _cuda_available():
            try:
                self._model = WhisperModel(str(path), device="cuda", compute_type="float16",
                                           local_files_only=True)
                self.device = "cuda"
            except Exception as e:  # CUDA 런타임(cuBLAS/cuDNN) 미설치 등
                log.warning("CUDA 로드 실패, CPU로 전환: %s", e)
        if self._model is None:
            self._model = WhisperModel(str(path), device="cpu", compute_type="int8",
                                       cpu_threads=os.cpu_count() or 4, local_files_only=True)
            self.device = "cpu"
        self._model_key = key
        return self._model

    def transcribe(
        self,
        audio_path: Path,
        size: str = DEFAULT_MODEL,
        on_progress: Callable[[float], None] | None = None,
        is_cancelled: Callable[[], bool] | None = None,
    ) -> list[Segment]:
        model = self._load(size)
        segments, info = model.transcribe(
            str(audio_path),
            language="ko",
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 2000},
            condition_on_previous_text=False,
        )
        total = info.duration or 0
        result: list[Segment] = []
        for s in segments:
            if is_cancelled and is_cancelled():
                raise TranscriptionCancelled()
            text = s.text.strip()
            if text:
                result.append(Segment(round(s.start, 2), round(s.end, 2), text))
            if on_progress and total > 0:
                on_progress(min(s.end / total, 1.0))
        if on_progress:
            on_progress(1.0)
        return result
