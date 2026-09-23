"""UI 스모크 테스트: 임시 데이터 폴더에 샘플을 넣고 실제 변환 파이프라인을 돌린 뒤 각 화면을 캡처한다.

python -m scripts.ui_smoke [ko|en]  → shots/*.png (en 이면 shots/*_en.png)
"""
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ["MEMOO_DATA_DIR"] = tempfile.mkdtemp(prefix="memoo-ui-")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from memo_o import db as dbm  # noqa: E402
from memo_o import i18n  # noqa: E402
from memo_o.db import Database, Segment  # noqa: E402
from memo_o.paths import db_path, recordings_dir  # noqa: E402
from memo_o.transcription import TranscriptionService  # noqa: E402
from memo_o.ui import theme  # noqa: E402
from memo_o.ui.dialogs import settings_dialog  # noqa: E402
from memo_o.ui.main_window import MainWindow  # noqa: E402

SHOTS = ROOT / "shots"
SHOTS.mkdir(exist_ok=True)
LANG = sys.argv[1] if len(sys.argv) > 1 else "ko"
SUFFIX = "" if LANG == "ko" else f"_{LANG}"


def seed(db: Database) -> int:
    base = datetime(2026, 9, 18, 9, 30)
    demo = [
        ("브레인스토밍", 8, 2702, dbm.DONE),
        ("주간 회고", 7, 1510, dbm.DONE),
        ("고객 상담", 3, 725, dbm.ERROR),
        ("강의 노트", 1, 1124, dbm.DONE),
    ]
    for title, days, dur, status in demo:
        p = recordings_dir() / f"demo_{days}.wav"
        shutil.copy(ROOT / "samples" / "tts_ko.wav", p)
        rid = db.create_recording(title, p, base - timedelta(days=days))
        db.update(rid, duration=dur, status=status)
        if status == dbm.DONE:
            db.save_transcript(rid, [Segment(0, 5, f"{title} 첫 문장입니다."), Segment(5, 9, "두 번째 문장입니다.")], "small")
        if status == dbm.ERROR:
            db.update(rid, error="모델을 불러오지 못했습니다.")
    for i in range(6):
        p = recordings_dir() / f"old_{i}.wav"
        shutil.copy(ROOT / "samples" / "tts_ko.wav", p)
        rid = db.create_recording(f"아이디어 메모 {i + 1}", p, base - timedelta(days=20 + i))
        db.update(rid, duration=300 + i * 60, status=dbm.DONE)
    # 실제로 변환할 녹음 (TTS 한국어 샘플)
    p = recordings_dir() / "tts.wav"
    shutil.copy(ROOT / "samples" / "tts_ko.wav", p)
    rid = db.create_recording("아이디어 메모", p, base)
    db.update(rid, duration=11.0, status=dbm.PENDING)
    return rid


def main() -> None:
    app = QApplication(sys.argv[:1])
    i18n.set_language(LANG)
    app.setStyle("Fusion")
    app.setFont(theme.app_font())
    app.setStyleSheet(theme.set_mode("light"))
    db = Database(db_path())
    db.set_setting("notice_ack", "1")
    rid = seed(db)
    stt = TranscriptionService(db)
    stt.start()
    win = MainWindow(db, stt)
    win.show()
    stt.enqueue(rid)

    steps = []

    def shot(name):
        app.processEvents()
        win.grab().save(str(SHOTS / f"{name}{SUFFIX}.png"))
        print("shot", name)

    def wait_done():
        rec = db.get(rid)
        if rec.status in (dbm.DONE, dbm.ERROR):
            print("transcription:", rec.status, rec.error, repr(rec.transcript))
            QTimer.singleShot(0, run_next)
        else:
            QTimer.singleShot(300, wait_done)

    def main_idle():
        shot("1_main")

    def list_page():
        win.open_list()
        shot("2_list")

    def list_search():
        win.list_page.search.setText("강의")
        win.list_page._search_changed()
        shot("2_list_search")
        win.list_page.search.clear()
        win.list_page._search_changed()

    def detail():
        win.open_recording(rid)
        shot("3_detail")

    def detail_search():
        win.detail_page.search.setText("안건")
        shot("3_detail_search")
        win.detail_page.search.clear()

    def detail_error():
        err_id = [r.id for r in db.list(limit=50) if r.status == dbm.ERROR][0]
        win.open_recording(err_id)
        shot("3_detail_error")

    def recording():
        win.open_main()
        win.record_page.start()
        QTimer.singleShot(1500, lambda: (shot("1_main_recording"), run_next()))

    def stop_recording():
        win.record_page.stop(ask_title=False)
        shot("1_main_after")
        rec = db.list(limit=1)[0]
        print("recorded:", rec.title, f"{rec.duration:.2f}s", rec.status, rec.file_path.exists())

    def settings():
        def grab_and_close():
            d = QApplication.activeModalWidget()
            d.grab().save(str(SHOTS / f"4_settings{SUFFIX}.png"))
            print("shot 4_settings")
            d.reject()
        QTimer.singleShot(400, grab_and_close)
        settings_dialog(win, db, stt.device)

    def finish():
        stt.shutdown()
        app.quit()

    steps[:] = [main_idle, wait_done, list_page, list_search, detail, detail_search, detail_error,
                recording, stop_recording, settings, finish]

    def run_next():
        if steps:
            step = steps.pop(0)
            step()
            if step not in (wait_done, recording, finish):
                QTimer.singleShot(200, run_next)

    QTimer.singleShot(500, run_next)
    app.exec()


if __name__ == "__main__":
    main()
