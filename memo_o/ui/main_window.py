import os

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QLabel, QMenu, QMessageBox, QStackedWidget, QVBoxLayout, QWidget,
)

from ..db import Database
from ..paths import data_dir
from ..transcription import TranscriptionService
from . import theme
from .detail_page import DetailPage
from .dialogs import about_dialog, settings_dialog
from .list_page import ListPage
from .record_page import RecordPage
from .edge_resize import EdgeResizer
from .widgets import TitleBar


class MainWindow(QWidget):
    def __init__(self, db: Database, stt: TranscriptionService):
        super().__init__()
        self.db = db
        self.stt = stt
        self.setObjectName("Root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setWindowTitle("MemoO")
        self.setMinimumSize(theme.WINDOW_W, theme.WINDOW_H)
        self.resize(theme.WINDOW_W, theme.WINDOW_H)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.title_bar = TitleBar(self)
        self.title_bar.back_clicked.connect(self.open_list)
        self.title_bar.menu_clicked.connect(self._show_menu)
        lay.addWidget(self.title_bar)

        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.record_page = RecordPage(self)
        self.list_page = ListPage(self)
        self.detail_page = DetailPage(self)
        for p in (self.record_page, self.list_page, self.detail_page):
            self.stack.addWidget(p.widget)
        self.current = self.record_page

        self._toast = QLabel(self)
        self._toast.setStyleSheet(
            "background: rgba(32,32,32,0.9); color: #FFFFFF; border-radius: 6px; padding: 8px 14px; font-size: 12px;"
        )
        self._toast.hide()
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._toast.hide)

        stt.changed.connect(self._on_stt_changed)
        stt.progress.connect(self._on_stt_progress)

        space = QShortcut(QKeySequence(Qt.Key_Space), self)
        space.setContext(Qt.WindowShortcut)
        space.activated.connect(self._space)
        esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        esc.activated.connect(self._escape)

        self._resizer = EdgeResizer(self)
        self.open_main()

    # --- 네비게이션 (페이지에서 ctx로 호출) ---
    def _show(self, page) -> None:
        if self.current is self.detail_page and page is not self.detail_page:
            self.detail_page.release()
        self.current = page
        self.stack.setCurrentWidget(page.widget)
        if page is not self.detail_page:
            page.refresh()
        self.update_title()

    def open_main(self) -> None:
        self._show(self.record_page)

    def open_list(self) -> None:
        self._show(self.list_page)

    def open_recording(self, rec_id: int) -> None:
        if not self.detail_page.load(rec_id):
            self.toast("녹음을 찾을 수 없습니다.")
            self.open_list()
            return
        self._show(self.detail_page)

    def update_title(self) -> None:
        if self.current is self.detail_page:
            self.title_bar.set_back_title(self.detail_page.title())
        else:
            self.title_bar.set_title(self.current.title())
        if self.record_page.is_recording:
            self.setWindowTitle("● 녹음 중 - MemoO")
        else:
            self.setWindowTitle(self.current.title() or "MemoO")

    def recording_state_changed(self, _recording: bool) -> None:
        self.update_title()

    def toast(self, msg: str, ms: int = 2000) -> None:
        self._toast.setText(msg)
        self._toast.adjustSize()
        self._toast.move((self.width() - self._toast.width()) // 2, self.height() - self._toast.height() - 60)
        self._toast.raise_()
        self._toast.show()
        self._toast_timer.start(ms)

    # --- 변환 서비스 이벤트 ---
    def _on_stt_changed(self, rec_id: int) -> None:
        if self.current is self.list_page:
            self.list_page.refresh()
        elif self.current is self.record_page:
            self.record_page.refresh()
        self.detail_page.reload_if_current(rec_id)

    def _on_stt_progress(self, rec_id: int, p: float) -> None:
        if self.current is self.list_page:
            self.list_page.on_progress(rec_id, p)
        elif self.current is self.detail_page:
            self.detail_page.on_progress(rec_id, p)

    # --- 메뉴 / 단축키 ---
    def _show_menu(self) -> None:
        m = QMenu(self)
        if self.current is self.detail_page:
            for a in self.detail_page.menu_actions(m):
                m.addAction(a)
            m.addSeparator()
        m.addAction("설정", self._settings)
        m.addAction("마이크 목록 새로고침", self._reload_mics)
        m.addAction("데이터 폴더 열기", lambda: os.startfile(data_dir()))
        m.addSeparator()
        m.addAction("MemoO 정보", lambda: about_dialog(self))
        btn = self.title_bar.menu_btn
        m.exec(btn.mapToGlobal(QPoint(btn.width() - m.sizeHint().width(), btn.height())))

    def _settings(self) -> None:
        if settings_dialog(self, self.db, self.stt.device):
            self.toast("다음 변환부터 새 모델이 적용됩니다.")

    def _reload_mics(self) -> None:
        if self.record_page.is_recording:
            self.toast("녹음 중에는 마이크를 바꿀 수 없습니다.")
            return
        self.record_page.reload_devices()
        self.toast("마이크 목록을 새로 불러왔습니다.")

    def _space(self) -> None:
        if self.current is self.record_page:
            self.record_page.toggle()
        elif self.current is self.detail_page:
            self.detail_page.toggle_play()

    def _escape(self) -> None:
        if self.current is self.detail_page:
            self.open_list()

    # --- 종료 ---
    def closeEvent(self, e) -> None:
        if self.record_page.is_recording:
            ans = QMessageBox.question(
                self, "녹음 중", "녹음 중입니다. 녹음을 저장하고 종료할까요?",
                QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Yes,
            )
            if ans != QMessageBox.Yes:
                e.ignore()
                return
            self.record_page.stop(ask_title=False)
        self.detail_page.player.stop()
        e.accept()

    def changeEvent(self, e) -> None:
        if e.type() == QEvent.WindowStateChange:
            self.title_bar.max_btn.setText("❐" if self.isMaximized() else "□")
            self.title_bar.max_btn.setToolTip("이전 크기로" if self.isMaximized() else "최대화")
        super().changeEvent(e)
