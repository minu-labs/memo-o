"""다운로드 페이지용 스크린샷(web/public/screens) 생성: python -m scripts.web_screens"""
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ["MEMOO_DATA_DIR"] = tempfile.mkdtemp(prefix="memoo-web-")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from memo_o import db as dbm  # noqa: E402
from memo_o.db import Database, Segment  # noqa: E402
from memo_o.paths import db_path, recordings_dir  # noqa: E402
from memo_o.transcription import TranscriptionService  # noqa: E402
from memo_o.ui import theme  # noqa: E402
from memo_o.ui.main_window import MainWindow  # noqa: E402

OUT = ROOT / "web" / "public" / "screens"

LINES = [
    (0, "오늘 떠오른 앱 아이디어를 정리해 보려고 합니다."),
    (6, "첫 번째는 녹음이 끝나면 바로 텍스트로 바뀌는 기능이에요."),
    (13, "인터넷 없이 PC 안에서만 처리되니까 보안 걱정이 없습니다."),
    (21, "두 번째는 문장을 누르면 그 부분부터 다시 듣는 기능입니다."),
    (28, "강의나 상담 기록을 다시 찾아볼 때 특히 유용할 것 같아요."),
    (36, "마지막으로 텍스트랑 자막 파일로 내보내기를 넣으면 좋겠습니다."),
    (44, "다음 주까지 화면 시안을 먼저 만들어 보기로 하죠."),
]


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(theme.app_font())
    app.setStyleSheet(theme.QSS)
    db = Database(db_path())
    db.set_setting("notice_ack", "1")
    base = datetime(2026, 9, 18, 14, 20)
    items = [("강의 노트 - 데이터베이스 개론", 1, 3124), ("고객 상담", 3, 725), ("주간 회고", 6, 1510),
             ("브레인스토밍", 8, 2702)]
    for title, days, dur in items:
        p = recordings_dir() / f"{days}.wav"
        shutil.copy(ROOT / "samples" / "tts_ko.wav", p)
        rid = db.create_recording(title, p, base - timedelta(days=days))
        db.update(rid, duration=dur, status=dbm.PENDING)
        db.save_transcript(rid, [Segment(0, 3, title)], "small")
    p = recordings_dir() / "idea.wav"
    shutil.copy(ROOT / "samples" / "tts_ko.wav", p)
    rid = db.create_recording("아이디어 메모", p, base)
    db.update(rid, duration=52, status=dbm.PENDING)
    segs = [Segment(s, (LINES[i + 1][0] if i + 1 < len(LINES) else 52), t) for i, (s, t) in enumerate(LINES)]
    db.save_transcript(rid, segs, "small")

    stt = TranscriptionService(db)
    win = MainWindow(db, stt)
    win.show()
    OUT.mkdir(parents=True, exist_ok=True)

    def run():
        app.processEvents()
        win.grab().save(str(OUT / "main.png"))
        win.open_recording(rid)
        dp = win.detail_page
        dp.current_idx = 2
        dp._render()
        dp.slider.setValue(int(dp.slider.maximum() * 0.28))
        dp.clock.setText("00:14/00:52")
        app.processEvents()
        win.grab().save(str(OUT / "detail.png"))
        win.open_list()
        app.processEvents()
        win.grab().save(str(OUT / "list.png"))
        print("saved", OUT)
        app.quit()

    QTimer.singleShot(400, run)
    app.exec()


if __name__ == "__main__":
    main()
