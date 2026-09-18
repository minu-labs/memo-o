from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QCursor, QGuiApplication

MARGIN = 6

_CURSORS = {
    Qt.LeftEdge: Qt.SizeHorCursor, Qt.RightEdge: Qt.SizeHorCursor,
    Qt.TopEdge: Qt.SizeVerCursor, Qt.BottomEdge: Qt.SizeVerCursor,
    Qt.TopEdge | Qt.LeftEdge: Qt.SizeFDiagCursor, Qt.BottomEdge | Qt.RightEdge: Qt.SizeFDiagCursor,
    Qt.TopEdge | Qt.RightEdge: Qt.SizeBDiagCursor, Qt.BottomEdge | Qt.LeftEdge: Qt.SizeBDiagCursor,
}


class EdgeResizer(QObject):
    """프레임 없는 창의 가장자리 드래그 크기 조절. QWindow 레벨에서 마우스 이벤트를 가로챈다."""

    def __init__(self, widget):
        super().__init__(widget)
        self.widget = widget
        self._override = False
        widget.winId()
        widget.windowHandle().installEventFilter(self)

    def _edges(self, pos) -> Qt.Edges:
        w = self.widget
        if w.isMaximized() or w.isFullScreen():
            return Qt.Edges()
        x, y = pos.x(), pos.y()
        e = Qt.Edges()
        if x <= MARGIN:
            e |= Qt.LeftEdge
        elif x >= w.width() - MARGIN:
            e |= Qt.RightEdge
        if y <= MARGIN:
            e |= Qt.TopEdge
        elif y >= w.height() - MARGIN:
            e |= Qt.BottomEdge
        return e

    def _set_cursor(self, edges) -> None:
        shape = _CURSORS.get(edges)
        if shape is not None:
            if self._override:
                QGuiApplication.changeOverrideCursor(QCursor(shape))
            else:
                QGuiApplication.setOverrideCursor(QCursor(shape))
                self._override = True
        elif self._override:
            QGuiApplication.restoreOverrideCursor()
            self._override = False

    def eventFilter(self, obj, event) -> bool:
        t = event.type()
        if t == QEvent.MouseMove and not event.buttons():
            self._set_cursor(self._edges(event.position().toPoint()))
        elif t == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            edges = self._edges(event.position().toPoint())
            if edges:
                self.widget.windowHandle().startSystemResize(edges)
                return True
        elif t == QEvent.Leave and self._override:
            QGuiApplication.restoreOverrideCursor()
            self._override = False
        return False
