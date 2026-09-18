from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget,
)

from ..export import fmt_clock
from .widgets import Card, ClickableRow, StatusBadge, clear_layout, page_widget

PAGE_SIZE = 8


class ListPage:
    """화면 2. 녹음 목록 (카드형 스택 리스트)."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.page = 0
        self.badges: dict[int, StatusBadge] = {}
        self.widget = w = page_widget()

        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        strip = QFrame()
        strip.setObjectName("ToolStrip")
        sl = QHBoxLayout(strip)
        sl.setContentsMargins(14, 10, 14, 10)
        sl.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("검색 (제목, 내용)")
        self.search.setClearButtonEnabled(True)
        self.new_btn = QPushButton("+ 새 녹음")
        self.new_btn.setObjectName("Primary")
        self.new_btn.setCursor(Qt.PointingHandCursor)
        self.new_btn.clicked.connect(ctx.open_main)
        sl.addWidget(self.search, 1)
        sl.addWidget(self.new_btn)
        root.addWidget(strip)

        self.debounce = QTimer(w)
        self.debounce.setSingleShot(True)
        self.debounce.setInterval(250)
        self.debounce.timeout.connect(self._search_changed)
        self.search.textChanged.connect(self.debounce.start)

        self.card = Card()
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        self.rows = QVBoxLayout(inner)
        self.rows.setContentsMargins(0, 0, 0, 0)
        self.rows.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.viewport().setStyleSheet("background: transparent;")
        self.card.body.addWidget(scroll)
        wrap = QVBoxLayout()
        wrap.setContentsMargins(14, 12, 14, 12)
        wrap.addWidget(self.card)
        root.addLayout(wrap, 1)

        pager = QHBoxLayout()
        pager.setContentsMargins(0, 0, 0, 12)
        pager.setSpacing(8)
        self.prev_btn = QPushButton("< 이전")
        self.next_btn = QPushButton("다음 >")
        for b in (self.prev_btn, self.next_btn):
            b.setObjectName("PagerBtn")
            b.setCursor(Qt.PointingHandCursor)
            b.setFocusPolicy(Qt.NoFocus)
        self.page_lbl = QLabel()
        self.page_lbl.setObjectName("Pager")
        self.prev_btn.clicked.connect(lambda: self._go(self.page - 1))
        self.next_btn.clicked.connect(lambda: self._go(self.page + 1))
        pager.addStretch(1)
        pager.addWidget(self.prev_btn)
        pager.addWidget(self.page_lbl)
        pager.addWidget(self.next_btn)
        pager.addStretch(1)
        root.addLayout(pager)

    def title(self) -> str:
        return "MemoO - 녹음 목록"

    def _search_changed(self) -> None:
        self.page = 0
        self.refresh()

    def _go(self, page: int) -> None:
        self.page = page
        self.refresh()

    def _sync_new_btn(self) -> None:
        recording = self.ctx.record_page.is_recording
        self.new_btn.setText("● 녹음으로 돌아가기" if recording else "+ 새 녹음")
        self.new_btn.setObjectName("Danger" if recording else "Primary")
        self.new_btn.style().unpolish(self.new_btn)
        self.new_btn.style().polish(self.new_btn)

    def refresh(self) -> None:
        self._sync_new_btn()
        q = self.search.text()
        total = self.ctx.db.count(q)
        pages = max(1, -(-total // PAGE_SIZE))
        self.page = min(max(self.page, 0), pages - 1)
        recs = self.ctx.db.list(q, limit=PAGE_SIZE, offset=self.page * PAGE_SIZE)

        clear_layout(self.rows)
        self.badges.clear()
        if not recs:
            empty = QLabel("검색 결과가 없습니다." if q.strip() else "아직 녹음이 없습니다.")
            empty.setObjectName("Empty")
            empty.setAlignment(Qt.AlignCenter)
            self.rows.addWidget(empty)
        for i, r in enumerate(recs):
            row = ClickableRow(padding=(12, 10, 12, 10))
            col = QVBoxLayout()
            col.setSpacing(2)
            t = QLabel(r.title)
            t.setObjectName("RowTitle")
            t.setTextFormat(Qt.PlainText)
            t.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            sub = QLabel(f"{r.created_at:%m-%d} · {fmt_clock(r.duration)}")
            sub.setObjectName("RowSub")
            col.addWidget(t)
            col.addWidget(sub)
            row.lay.addLayout(col, 1)
            badge = StatusBadge(r.status, self.ctx.stt.progress_of(r.id))
            self.badges[r.id] = badge
            row.lay.addWidget(badge, 0, Qt.AlignVCenter)
            row.set_last(i == len(recs) - 1)
            row.clicked.connect(lambda rid=r.id: self.ctx.open_recording(rid))
            self.rows.addWidget(row)
        self.rows.addStretch(1)

        self.page_lbl.setText(f"<b style='color:#1A1A1A'>{self.page + 1} / {pages}</b>")
        self.prev_btn.setEnabled(self.page > 0)
        self.next_btn.setEnabled(self.page < pages - 1)

    def on_progress(self, rec_id: int, p: float) -> None:
        badge = self.badges.get(rec_id)
        if badge is not None:
            rec = self.ctx.db.get(rec_id)
            if rec:
                badge.set_status(rec.status, p)
