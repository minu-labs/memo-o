from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QPushButton, QWidget,
)

from . import theme

THEMES = {
    "dark": dict(bg="#202020", fg="#FFFFFF", sub="#C9C9C9", divider="rgba(255,255,255,0.16)",
                 hover="rgba(255,255,255,0.14)"),
    "light": dict(bg="#FFFFFF", fg="#1A1A1A", sub="#616161", divider="#E5E5E5", hover="#F2F2F2"),
}
DRAG_THRESHOLD = 4


class CompactWindow(QWidget):
    """녹음 중 최소화 시 뜨는 작은 캡슐형 창 (항상 위, 드래그 이동 가능)."""

    restore_clicked = Signal()
    stop_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("Compact")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowTitle("MemoO - 녹음 중")
        self.setFixedSize(300, 56)
        self._drag_start = None
        self._win_start = None
        self._dragged = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 8, 0)
        lay.setSpacing(10)

        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        self._dot_effect = QGraphicsOpacityEffect(self.dot)
        self.dot.setGraphicsEffect(self._dot_effect)
        self._dot_anim = QPropertyAnimation(self._dot_effect, b"opacity", self)
        self._dot_anim.setStartValue(1.0)
        self._dot_anim.setEndValue(0.35)
        self._dot_anim.setDuration(700)
        self._dot_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._dot_anim.finished.connect(self._flip_dot)
        lay.addWidget(self.dot)

        self.time_lbl = QLabel("00:00:00")
        self.time_lbl.setObjectName("CompactTime")
        lay.addWidget(self.time_lbl, 1)

        self.divider = QFrame()
        self.divider.setObjectName("CompactDivider")
        self.divider.setFixedWidth(1)
        self.divider.setFixedHeight(24)
        lay.addWidget(self.divider)

        self.stop_btn = QPushButton()
        self.stop_btn.setObjectName("CompactStop")
        self.stop_btn.setFixedSize(34, 34)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setToolTip("녹음 중지")
        self.stop_btn.setFocusPolicy(Qt.NoFocus)
        stop_icon = QFrame(self.stop_btn)
        stop_icon.setFixedSize(12, 12)
        stop_icon.setStyleSheet("background:#FFFFFF; border-radius:3px;")
        sl = QHBoxLayout(self.stop_btn)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.addWidget(stop_icon, 0, Qt.AlignCenter)
        self.stop_btn.clicked.connect(self.stop_clicked)
        lay.addWidget(self.stop_btn)

        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("CompactMin")
        self.min_btn.setFixedSize(34, 34)
        self.min_btn.setCursor(Qt.PointingHandCursor)
        self.min_btn.setToolTip("작업표시줄로 최소화")
        self.min_btn.setFocusPolicy(Qt.NoFocus)
        self.min_btn.clicked.connect(self.showMinimized)
        lay.addWidget(self.min_btn)

        self.set_theme("light")

    def set_time(self, text: str) -> None:
        self.time_lbl.setText(text)

    def set_theme(self, mode: str) -> None:
        t = THEMES.get(mode, THEMES["dark"])
        self.setStyleSheet(f"""
            #Compact {{ background: {t['bg']}; border-radius: 28px; }}
            QLabel#CompactTime {{ color: {t['fg']}; font-size: 16px; font-weight: 700; }}
            QFrame#CompactDivider {{ background: {t['divider']}; border: none; }}
            QPushButton#CompactStop {{ background: {theme.RED}; border: none; border-radius: 17px; }}
            QPushButton#CompactStop:hover {{ background: #B92B2E; }}
            QPushButton#CompactMin {{ background: transparent; border: none; border-radius: 17px;
                                       color: {t['sub']}; font-size: 13px; }}
            QPushButton#CompactMin:hover {{ background: {t['hover']}; }}
        """)
        self.dot.setStyleSheet(f"background: {theme.RED}; border-radius: 5px;")

    def _flip_dot(self) -> None:
        forward = self._dot_anim.direction() == QAbstractAnimation.Forward
        self._dot_anim.setDirection(QAbstractAnimation.Backward if forward else QAbstractAnimation.Forward)
        self._dot_anim.start()

    def showEvent(self, e) -> None:
        self._dot_anim.setDirection(QAbstractAnimation.Forward)
        self._dot_anim.start()
        super().showEvent(e)

    def hideEvent(self, e) -> None:
        self._dot_anim.stop()
        super().hideEvent(e)

    # --- 드래그 이동 / 클릭 시 복귀 ---
    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.LeftButton:
            self._drag_start = e.globalPosition().toPoint()
            self._win_start = self.pos()
            self._dragged = False
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e) -> None:
        if e.buttons() & Qt.LeftButton and self._drag_start is not None:
            delta = e.globalPosition().toPoint() - self._drag_start
            if delta.manhattanLength() > DRAG_THRESHOLD:
                self._dragged = True
                self.move(self._win_start + delta)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e) -> None:
        if e.button() == Qt.LeftButton and self._drag_start is not None:
            if not self._dragged:
                self.restore_clicked.emit()
            self._drag_start = None
        super().mouseReleaseEvent(e)
