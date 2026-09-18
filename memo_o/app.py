import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QLockFile, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from . import APP_NAME, __version__
from .db import Database
from .paths import data_dir, db_path, resource_dir
from .transcription import TranscriptionService

log = logging.getLogger("memo_o")


def _setup_logging() -> None:
    handler = RotatingFileHandler(data_dir() / "memo-o.log", maxBytes=1_000_000, backupCount=2,
                                  encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    if sys.stderr is not None:
        root.addHandler(logging.StreamHandler())


def _excepthook(exc_type, exc, tb) -> None:
    log.error("처리되지 않은 오류:\n%s", "".join(traceback.format_exception(exc_type, exc, tb)))
    if QApplication.instance():
        QMessageBox.critical(None, APP_NAME, f"예상치 못한 오류가 발생했습니다.\n{exc}\n\n로그: {data_dir() / 'memo-o.log'}")


def main() -> int:
    _setup_logging()
    sys.excepthook = _excepthook
    log.info("MemoO %s 시작", __version__)

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")

    from .ui import theme
    app.setFont(theme.app_font())
    app.setStyleSheet(theme.QSS)
    icon = resource_dir() / "memo-o.ico"
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))

    lock = QLockFile(str(data_dir() / "memo-o.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None, APP_NAME, "MemoO가 이미 실행 중입니다.")
        return 0

    db = Database(db_path())
    stt = TranscriptionService(db)
    stt.start()

    from .ui.dialogs import first_run_notice
    from .ui.main_window import MainWindow

    win = MainWindow(db, stt)
    win.show()
    if db.get_setting("notice_ack") != "1" and first_run_notice(win):
        db.set_setting("notice_ack", "1")

    code = app.exec()
    stt.shutdown()
    db.close()
    lock.unlock()
    log.info("종료")
    return code
