import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QLibraryInfo, QLockFile, Qt, QTranslator
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from . import APP_NAME, __version__, i18n
from .db import Database
from .i18n import tr
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
        QMessageBox.critical(None, APP_NAME, tr("app.unhandled_error", exc=exc, log=data_dir() / "memo-o.log"))


def main() -> int:
    _setup_logging()
    sys.excepthook = _excepthook
    log.info("MemoO %s 시작", __version__)

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")

    db = Database(db_path())
    i18n.set_language(i18n.resolve(db.get_setting("ui_lang")))
    # QMessageBox 예/아니요 등 Qt 기본 버튼 문구 번역 (없으면 영어로 표시)
    qt_tr = QTranslator(app)
    if qt_tr.load(f"qtbase_{i18n.language()}", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(qt_tr)

    from .ui import theme
    app.setFont(theme.app_font())
    icon = resource_dir() / "memo-o.ico"
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))

    lock = QLockFile(str(data_dir() / "memo-o.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None, APP_NAME, tr("app.already_running"))
        db.close()
        return 0

    app.setStyleSheet(theme.set_mode(db.get_setting("theme", "light")))
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
