from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractButton, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from .. import __version__
from .. import db as dbm
from . import theme


class TitleBar(QFrame):
    """32px 다크 타이틀바. 드래그로 이동, 더블클릭으로 최대화."""

    back_clicked = Signal()
    menu_clicked = Signal()
    record_indicator_clicked = Signal()
    minimize_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(32)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 0, 0)
        lay.setSpacing(0)

        self.title = QLabel("MemoO")
        self.title.setObjectName("TitleText")
        self.version_lbl = QLabel(f"v{__version__}")
        self.version_lbl.setStyleSheet("color: #8A8A8A; font-size: 10px;")
        self.back = QPushButton()
        self.back.setObjectName("BackBtn")
        self.back.setCursor(Qt.PointingHandCursor)
        self.back.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.back.clicked.connect(self.back_clicked)
        self.back.hide()

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.addWidget(self.title)
        title_row.addWidget(self.version_lbl)
        lay.addLayout(title_row, 1)
        lay.addWidget(self.back, 1)

        self.rec_indicator = QPushButton()
        self.rec_indicator.setObjectName("RecIndicator")
        self.rec_indicator.setCursor(Qt.PointingHandCursor)
        self.rec_indicator.setToolTip("녹음 화면으로 돌아가기")
        self.rec_indicator.setFocusPolicy(Qt.NoFocus)
        self.rec_indicator.clicked.connect(self.record_indicator_clicked)
        self.rec_indicator.hide()
        lay.addWidget(self.rec_indicator)

        self.menu_btn = self._btn("⋯", "MenuBtn", "메뉴")
        self.menu_btn.setStyleSheet("font-size: 14px;")
        self.menu_btn.clicked.connect(self.menu_clicked)
        self.min_btn = self._btn("—", "MinBtn", "최소화")
        self.max_btn = self._btn("□", "MaxBtn", "최대화")
        self.close_btn = self._btn("✕", "CloseBtn", "닫기")
        for b in (self.menu_btn, self.min_btn, self.max_btn, self.close_btn):
            lay.addWidget(b)
        self.min_btn.clicked.connect(self.minimize_clicked)
        self.max_btn.clicked.connect(self.toggle_max)
        self.close_btn.clicked.connect(lambda: self.window().close())

    def _btn(self, text, name, tip):
        b = QPushButton(text)
        b.setObjectName(name)
        b.setToolTip(tip)
        b.setFocusPolicy(Qt.NoFocus)
        return b

    def set_title(self, text: str) -> None:
        self.back.hide()
        self.title.show()
        self.version_lbl.show()
        self.title.setText(text)

    def set_back_title(self, text: str) -> None:
        self.title.hide()
        self.version_lbl.hide()
        self.back.show()
        self.back.setText(f"←  {text}")
        self.back.setToolTip(text)

    def set_recording_active(self, active: bool) -> None:
        self.rec_indicator.setVisible(active)

    def set_recording_time(self, text: str) -> None:
        self.rec_indicator.setText(f"●  {text}")

    def toggle_max(self) -> None:
        w = self.window()
        w.showNormal() if w.isMaximized() else w.showMaximized()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.window().windowHandle().startSystemMove()
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.toggle_max()


class RecordButton(QAbstractButton):
    """지름 96px 빨간 원형 버튼. 대기=흰 원(36px), 녹음 중=흰 둥근 사각형(22px)."""

    SIZE = 96

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(self.SIZE + 8, self.SIZE + 8)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("녹음 시작/중지 (Space)")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(209, 52, 56, 100))
        self.setGraphicsEffect(shadow)

    def sizeHint(self):
        return QSize(self.SIZE + 8, self.SIZE + 8)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        red = QColor(theme.RED)
        if self.isDown():
            red = red.darker(115)
        elif self.underMouse():
            red = red.lighter(108)
        p.setBrush(red)
        c = self.rect().center().toPointF()
        r = self.SIZE / 2
        p.drawEllipse(c, r, r)
        p.setBrush(QColor("#FFFFFF"))
        if self.isChecked():
            s = 22
            p.drawRoundedRect(QRectF(c.x() - s / 2, c.y() - s / 2, s, s), 4, 4)
        else:
            p.drawEllipse(c, 18, 18)

    def enterEvent(self, e):
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.update()
        super().leaveEvent(e)


class LevelMeter(QWidget):
    """마이크 입력 레벨(0~1) 표시 바. 소리가 잘 들어오는지 눈으로 확인할 수 있게 한다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._level = 0.0
        self.setFixedHeight(6)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_level(self, level: float) -> None:
        level = max(0.0, min(1.0, level))
        if abs(level - self._level) < 0.01:
            return
        self._level = level
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        rect = QRectF(self.rect())
        p.setBrush(QColor(theme.SLIDER_GROOVE))
        p.drawRoundedRect(rect, 3, 3)
        if self._level > 0:
            fg = QColor(theme.RED) if self._level > 0.9 else QColor(theme.ACCENT)
            p.setBrush(fg)
            p.drawRoundedRect(QRectF(rect.x(), rect.y(), rect.width() * self._level, rect.height()), 3, 3)


def status_text(status: str, progress: float | None = None) -> str:
    if status == dbm.DONE:
        return "완료"
    if status == dbm.TRANSCRIBING:
        return f"변환 중 {progress:.0%}" if progress is not None else "변환 중"
    if status == dbm.PENDING:
        return "변환 대기"
    if status == dbm.RECORDING:
        return "녹음 중"
    return "오류"


class StatusBadge(QLabel):
    def __init__(self, status: str, progress: float | None = None, parent=None):
        super().__init__(parent)
        self.set_status(status, progress)

    def set_status(self, status: str, progress: float | None = None) -> None:
        if status == dbm.DONE:
            bg, fg = theme.DONE_BG, theme.DONE_FG
        elif status in (dbm.ERROR, dbm.RECORDING):
            bg, fg = theme.RED_SOFT, theme.RED
        else:
            bg, fg = theme.ING_BG, theme.ING_FG
        self.setText(status_text(status, progress))
        self.setStyleSheet(
            f"background:{bg}; color:{fg}; font-size:11px; padding:1px 7px; border-radius:4px;"
        )


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(0)


class ClickableRow(QFrame):
    clicked = Signal()

    def __init__(self, parent=None, padding=(12, 8, 12, 8)):
        super().__init__(parent)
        self.setObjectName("Row")
        self.setProperty("clickable", True)
        self.setCursor(Qt.PointingHandCursor)
        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(*padding)
        self.lay.setSpacing(8)

    def set_last(self, last: bool) -> None:
        self.setProperty("last", last)
        self.style().unpolish(self)
        self.style().polish(self)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(e)


def link_button(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("Link")
    b.setCursor(Qt.PointingHandCursor)
    b.setFocusPolicy(Qt.NoFocus)
    return b


def clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.deleteLater()


def page_widget() -> QWidget:
    w = QWidget()
    w.setObjectName("Page")
    w.setAttribute(Qt.WA_StyledBackground, True)
    return w
