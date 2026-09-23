import logging
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QInputDialog, QLabel, QMessageBox, QSizePolicy, QVBoxLayout,
)

from .. import db as dbm
from ..export import fmt_hms
from ..i18n import tr
from ..paths import recordings_dir
from ..recorder import Recorder, list_input_devices
from .widgets import (
    Card, ClickableRow, LevelMeter, RecordButton, StatusBadge, clear_layout, link_button, page_widget,
)

log = logging.getLogger(__name__)
RECENT_COUNT = 2


class RecordPage:
    """화면 1. 메인(녹음). QWidget 합성으로 구성."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.recorder: Recorder | None = None
        self.rec_id: int | None = None
        self.badges: dict[int, StatusBadge] = {}
        self.widget = w = page_widget()
        self.open_recording = ctx.open_recording
        self.open_list = ctx.open_list

        root = QVBoxLayout(w)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        self.button = RecordButton()
        self.button.clicked.connect(self.toggle)
        root.addWidget(self.button, 0, Qt.AlignHCenter)

        self.btn_label = QLabel(tr("rec.start"))
        self.btn_label.setObjectName("BtnLabel")
        root.addWidget(self.btn_label, 0, Qt.AlignHCenter)
        root.addSpacing(-8)

        meta = QHBoxLayout()
        meta.setSpacing(20)
        self.status_lbl = QLabel()
        self.status_lbl.setObjectName("Meta")
        self.time_lbl = QLabel()
        self.time_lbl.setObjectName("Meta")
        meta.addStretch(1)
        meta.addWidget(self.status_lbl)
        meta.addWidget(self.time_lbl)
        meta.addStretch(1)
        root.addLayout(meta)

        mic = QHBoxLayout()
        mic.setSpacing(8)
        mic_lbl = QLabel(tr("rec.mic"))
        mic_lbl.setObjectName("Meta")
        self.mic_combo = QComboBox()
        self.mic_combo.setMaximumWidth(300)
        self.mic_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.mic_combo.setMinimumContentsLength(10)
        mic.addStretch(1)
        mic.addWidget(mic_lbl)
        mic.addWidget(self.mic_combo)
        mic.addStretch(1)
        root.addLayout(mic)

        level_row = QHBoxLayout()
        level_row.setContentsMargins(40, 0, 40, 0)
        self.level_meter = LevelMeter()
        self.level_meter.hide()
        level_row.addWidget(self.level_meter)
        root.addLayout(level_row)

        self.recent = Card()
        header = QFrame()
        header.setObjectName("CardHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 10, 12, 10)
        title = QLabel(tr("rec.recent"))
        title.setObjectName("CardTitle")
        hl.addWidget(title)
        self.recent.body.addWidget(header)
        self.recent_rows = QVBoxLayout()
        self.recent_rows.setSpacing(0)
        self.recent.body.addLayout(self.recent_rows)
        self.recent.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        root.addSpacing(4)
        root.addWidget(self.recent)

        all_link = link_button(tr("rec.view_all"))
        all_link.clicked.connect(self.open_list)
        root.addWidget(all_link, 0, Qt.AlignHCenter)
        root.addStretch(1)

        self.timer = QTimer(w)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._tick)

        self._set_idle_ui()
        self.reload_devices()

    # --- 공개 API ---
    @property
    def is_recording(self) -> bool:
        return self.recorder is not None

    def title(self) -> str:
        return "MemoO"

    def refresh(self) -> None:
        clear_layout(self.recent_rows)
        self.badges = {}
        recs = self.ctx.db.list(limit=RECENT_COUNT)
        if not recs:
            empty = QLabel(tr("rec.empty"))
            empty.setObjectName("Empty")
            empty.setWordWrap(True)
            self.recent_rows.addWidget(empty)
            return
        for i, r in enumerate(recs):
            row = ClickableRow()
            text = QLabel(f"{r.created_at:%m-%d}   {r.title}")
            text.setTextFormat(Qt.PlainText)
            text.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            row.lay.addWidget(text, 1)
            if r.status != dbm.DONE:
                badge = StatusBadge(r.status, self.ctx.stt.progress_of(r.id))
                self.badges[r.id] = badge
                row.lay.addWidget(badge)
            open_lbl = QLabel(tr("rec.open"))
            open_lbl.setObjectName("Link")
            row.lay.addWidget(open_lbl)
            row.set_last(i == len(recs) - 1)
            row.clicked.connect(lambda rid=r.id: self.open_recording(rid))
            self.recent_rows.addWidget(row)

    def on_progress(self, rec_id: int, p: float) -> None:
        badge = self.badges.get(rec_id)
        if badge is not None:
            rec = self.ctx.db.get(rec_id)
            if rec:
                badge.set_status(rec.status, p)

    def reload_devices(self) -> None:
        current = self.mic_combo.currentData()
        self.mic_combo.clear()
        for d in list_input_devices():
            self.mic_combo.addItem(d.name, d.index)
            self.mic_combo.setItemData(self.mic_combo.count() - 1, d.name, Qt.ToolTipRole)
        saved = self.ctx.db.get_setting("mic_name")
        idx = self.mic_combo.findText(saved) if saved else -1
        if idx < 0 and current is not None:
            idx = self.mic_combo.findData(current)
        self.mic_combo.setCurrentIndex(max(idx, 0))

    def toggle(self) -> None:
        if self.is_recording:
            self.stop()
        else:
            self.start()

    def start(self) -> None:
        now = datetime.now()
        path = recordings_dir() / f"{now:%Y%m%d_%H%M%S}.wav"
        n = 1
        while path.exists():
            path = recordings_dir() / f"{now:%Y%m%d_%H%M%S}_{n}.wav"
            n += 1
        device = self.mic_combo.currentData()
        rec = Recorder(path, device)
        try:
            rec.start()
        except Exception as e:
            log.exception("녹음 시작 실패")
            self.button.setChecked(False)
            path.unlink(missing_ok=True)
            QMessageBox.warning(self.widget, tr("rec.start_failed_title"), tr("rec.start_failed", e=e))
            return
        self.ctx.db.set_setting("mic_name", self.mic_combo.currentText())
        self.recorder = rec
        self.rec_id = self.ctx.db.create_recording(tr("rec.default_title", date=f"{now:%m-%d %H:%M}"), path, now)
        self.button.setChecked(True)
        self.btn_label.setText(tr("rec.stop"))
        self.status_lbl.setText(tr("rec.status_recording"))
        self.mic_combo.setEnabled(False)
        self.level_meter.set_level(0.0)
        self.level_meter.show()
        self.timer.start()
        self._tick()
        self.ctx.recording_state_changed(True)
        self.refresh()

    def stop(self, ask_title: bool = True) -> None:
        if not self.recorder:
            return
        self.timer.stop()
        duration = self.recorder.stop()
        failed_msg = self.recorder.error if self.recorder.failed else None
        rid = self.rec_id
        self.recorder = None
        self.rec_id = None
        self._set_idle_ui()
        self.ctx.db.update(rid, duration=duration)
        if ask_title:
            rec = self.ctx.db.get(rid)
            title, ok = QInputDialog.getText(self.widget, tr("rec.save_title"), tr("rec.enter_title"), text=rec.title)
            if ok and title.strip():
                self.ctx.db.update(rid, title=title.strip()[:100])
        self.ctx.stt.enqueue(rid)
        self.ctx.recording_state_changed(False)
        self.refresh()
        if failed_msg:
            QMessageBox.warning(self.widget, tr("rec.interrupted_title"), tr("rec.interrupted", msg=failed_msg))

    # --- 내부 ---
    def _set_idle_ui(self) -> None:
        self.button.setChecked(False)
        self.btn_label.setText(tr("rec.start"))
        self.status_lbl.setText(tr("rec.status_idle"))
        self.time_lbl.setText(tr("rec.time", t="00:00:00"))
        self.mic_combo.setEnabled(True)
        self.level_meter.hide()

    def _tick(self) -> None:
        if not self.recorder:
            return
        self.time_lbl.setText(tr("rec.time", t=fmt_hms(self.recorder.elapsed)))
        self.ctx.update_recording_time(self.recorder.elapsed)
        self.level_meter.set_level(self.recorder.level)
        if self.recorder.failed:
            self.stop(ask_title=False)
