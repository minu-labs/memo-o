import bisect
import html
import logging
import re
import shutil
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QUrl
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMenu, QMessageBox,
    QPushButton, QSlider, QTextBrowser, QVBoxLayout,
)

from .. import db as dbm
from ..db import Recording, Segment
from ..export import fmt_clock, to_srt, to_txt
from . import theme
from .widgets import page_widget, status_text

log = logging.getLogger(__name__)
SKIP_MS = 10_000


def _safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", name).strip() or "memo"


class DetailPage:
    """화면 3. 녹음 상세."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.rec: Recording | None = None
        self.segments: list[Segment] = []
        self.starts: list[float] = []
        self.current_idx = -1
        self.duration_ms = 0
        self._seeking = False
        self.widget = w = page_widget()

        self.player = QMediaPlayer(w)
        self.audio = QAudioOutput(w)
        self.player.setAudioOutput(self.audio)
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.errorOccurred.connect(self._on_error)

        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 재생 컨트롤
        ctrl = QFrame()
        ctrl.setObjectName("ToolStrip")
        cl = QHBoxLayout(ctrl)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(8)
        self.back_btn = self._ctrl("◀◀", "Ctrl", "10초 뒤로")
        self.play_btn = self._ctrl("▶", "Play", "재생 / 일시정지")
        self.fwd_btn = self._ctrl("▶▶", "Ctrl", "10초 앞으로")
        self.back_btn.clicked.connect(lambda: self._skip(-SKIP_MS))
        self.fwd_btn.clicked.connect(lambda: self._skip(SKIP_MS))
        self.play_btn.clicked.connect(self.toggle_play)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setCursor(Qt.PointingHandCursor)
        self.slider.sliderPressed.connect(lambda: setattr(self, "_seeking", True))
        self.slider.sliderReleased.connect(self._slider_released)
        self.slider.sliderMoved.connect(lambda v: self.clock.setText(self._clock_text(v)))
        self.clock = QLabel("00:00/00:00")
        self.clock.setObjectName("Clock")
        for b in (self.back_btn, self.play_btn, self.fwd_btn):
            cl.addWidget(b)
        cl.addSpacing(6)
        cl.addWidget(self.slider, 1)
        cl.addSpacing(6)
        cl.addWidget(self.clock)
        root.addWidget(ctrl)

        # 내용 검색
        sf = QFrame()
        sf.setObjectName("ToolStrip")
        sfl = QHBoxLayout(sf)
        sfl.setContentsMargins(16, 8, 16, 8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("내용 검색")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _: self._render())
        sfl.addWidget(self.search)
        root.addWidget(sf)

        # 트랜스크립트
        self.view = QTextBrowser()
        self.view.setObjectName("Transcript")
        self.view.setOpenLinks(False)
        self.view.anchorClicked.connect(self._on_anchor)
        self.view.document().setDocumentMargin(8)
        root.addWidget(self.view, 1)

        # 하단 액션
        bar = QFrame()
        bar.setObjectName("ActionBar")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(16, 10, 16, 10)
        bl.setSpacing(8)
        self.export_btn = QPushButton("내보내기")
        self.export_btn.setObjectName("Primary")
        self.export_btn.setStyleSheet("padding: 8px 6px;")
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.setObjectName("Danger")
        for b in (self.export_btn, self.delete_btn):
            b.setCursor(Qt.PointingHandCursor)
            bl.addWidget(b, 1)
        self.export_btn.clicked.connect(self._export_menu)
        self.delete_btn.clicked.connect(self.delete)
        root.addWidget(bar)

    def _ctrl(self, text, name, tip) -> QPushButton:
        b = QPushButton(text)
        b.setObjectName(name)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.setFocusPolicy(Qt.NoFocus)
        return b

    # --- 공개 API ---
    def title(self) -> str:
        if not self.rec:
            return ""
        return f"{self.rec.title} · {self.rec.created_at:%m-%d}"

    def load(self, rec_id: int) -> bool:
        rec = self.ctx.db.get(rec_id)
        if rec is None:
            return False
        if self.rec is None or self.rec.id != rec_id:
            self.player.stop()
            self.search.clear()
            self.duration_ms = int(rec.duration * 1000)
            self.slider.setRange(0, self.duration_ms)
            self.slider.setValue(0)
            self.player.setSource(QUrl.fromLocalFile(str(rec.file_path)))
            self.current_idx = -1
        self.rec = rec
        self.segments = self.ctx.db.segments(rec_id)
        self.starts = [s.start for s in self.segments]
        has_audio = rec.file_path.exists() and rec.status != dbm.RECORDING
        for b in (self.play_btn, self.back_btn, self.fwd_btn, self.slider):
            b.setEnabled(has_audio)
        self.clock.setText(self._clock_text(self.player.position()))
        self._render()
        return True

    def reload_if_current(self, rec_id: int) -> None:
        if self.rec and self.rec.id == rec_id:
            self.load(rec_id)

    def on_progress(self, rec_id: int, _p: float) -> None:
        if self.rec and self.rec.id == rec_id and not self.segments:
            self._render()

    def release(self) -> None:
        """다른 화면으로 나갈 때 재생 중지."""
        self.player.pause()

    def menu_actions(self, parent) -> list[QAction]:
        a = QAction("제목 변경", parent)
        a.triggered.connect(self.rename)
        return [a]

    def toggle_play(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def rename(self) -> None:
        if not self.rec:
            return
        title, ok = QInputDialog.getText(self.widget, "제목 변경", "새 제목", text=self.rec.title)
        if ok and title.strip():
            self.ctx.db.update(self.rec.id, title=title.strip()[:100])
            self.load(self.rec.id)
            self.ctx.update_title()

    def delete(self) -> None:
        if not self.rec:
            return
        ans = QMessageBox.question(
            self.widget, "녹음 삭제",
            f"'{self.rec.title}' 녹음과 변환된 텍스트를 삭제할까요?\n삭제한 녹음은 복구할 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        rec = self.rec
        self.ctx.stt.cancel(rec.id)
        self.player.stop()
        self.player.setSource(QUrl())
        self.rec = None
        self.ctx.db.delete(rec.id)
        try:
            rec.file_path.unlink(missing_ok=True)
        except OSError:
            log.exception("녹음 파일 삭제 실패: %s", rec.file_path)
        self.ctx.open_list()

    # --- 트랜스크립트 ---
    def _render(self) -> None:
        rec = self.rec
        if rec is None:
            self.view.clear()
            return
        if not self.segments:
            self.view.setHtml(self._status_html(rec))
            return
        q = self.search.text().strip()
        rows = []
        for i, s in enumerate(self.segments):
            if q and q.lower() not in s.text.lower():
                continue
            text = html.escape(s.text)
            if q:
                text = re.sub(
                    re.escape(html.escape(q)),
                    lambda m: f"<span style='background:#FFE58F; color:#1A1A1A'>{m.group(0)}</span>",
                    text, flags=re.IGNORECASE,
                )
            bg = f"background:{theme.ACCENT_SOFT};" if i == self.current_idx else ""
            cell = f"border-bottom:1px solid {theme.DIVIDER}; padding:6px 0; {bg}"
            rows.append(
                f"<tr><td width='46' valign='top' style='{cell}'>"
                f"<a name='seg{i}' href='seek:{i}' style='color:{theme.TEXT_MUTED}; text-decoration:none;'>"
                f"{fmt_clock(s.start)}</a></td>"
                f"<td style='{cell}'><a href='seek:{i}' style='color:{theme.TEXT}; text-decoration:none;'>"
                f"{text}</a></td></tr>"
            )
        if not rows:
            body = f"<p style='color:{theme.TEXT_MUTED}; font-size:12px;'>'{html.escape(q)}' 검색 결과가 없습니다.</p>"
        else:
            body = ("<table width='100%' cellspacing='0' cellpadding='0' style='border-collapse:collapse;"
                    " font-size:12px; line-height:150%;'>" + "".join(rows) + "</table>")
        sb = self.view.verticalScrollBar()
        pos = sb.value()
        self.view.setHtml(body)
        sb.setValue(pos)

    def _status_html(self, rec: Recording) -> str:
        style = f"color:{theme.TEXT_SUB}; font-size:12px; line-height:160%;"
        if rec.status == dbm.DONE:
            msg = "인식된 음성이 없습니다."
        elif rec.status == dbm.ERROR:
            msg = (f"텍스트 변환에 실패했습니다.<br><span style='color:{theme.RED}'>"
                   f"{html.escape(rec.error or '')}</span><br><br>"
                   f"<a href='retry:' style='color:{theme.ACCENT}; font-weight:600;'>다시 변환하기</a>")
        elif rec.status == dbm.TRANSCRIBING:
            p = self.ctx.stt.progress_of(rec.id)
            msg = (f"{status_text(rec.status, p)} — 텍스트로 변환하고 있습니다.<br>"
                   "변환이 끝나면 이 화면에 자동으로 표시됩니다. 녹음은 지금 바로 재생할 수 있습니다.")
        elif rec.status == dbm.PENDING:
            msg = "변환 대기 중입니다. 앞선 녹음의 변환이 끝나면 자동으로 시작됩니다."
        else:
            msg = "녹음 중입니다."
        return f"<p style='{style}'>{msg}</p>"

    def _on_anchor(self, url: QUrl) -> None:
        s = url.toString()
        if s.startswith("seek:"):
            seg = self.segments[int(s[5:])]
            self.player.setPosition(int(seg.start * 1000))
            if self.player.playbackState() != QMediaPlayer.PlayingState:
                self.player.play()
        elif s.startswith("retry:") and self.rec:
            self.ctx.stt.enqueue(self.rec.id)
            self.load(self.rec.id)

    # --- 플레이어 ---
    def _clock_text(self, pos_ms: int) -> str:
        return f"{fmt_clock(pos_ms / 1000)}/{fmt_clock(self.duration_ms / 1000)}"

    def _on_duration(self, d: int) -> None:
        if d > 0:
            self.duration_ms = d
            self.slider.setRange(0, d)
            self.clock.setText(self._clock_text(self.player.position()))

    def _on_position(self, pos: int) -> None:
        if not self._seeking:
            self.slider.setValue(pos)
            self.clock.setText(self._clock_text(pos))
        if self.starts:
            idx = bisect.bisect_right(self.starts, pos / 1000 + 0.05) - 1
            if idx != self.current_idx:
                self.current_idx = idx
                self._render()

    def _on_state(self, state) -> None:
        self.play_btn.setText("❚❚" if state == QMediaPlayer.PlayingState else "▶")

    def _on_error(self, _err, msg: str) -> None:
        log.warning("재생 오류: %s", msg)
        if self.rec:
            QMessageBox.warning(self.widget, "재생 오류", f"녹음 파일을 재생할 수 없습니다.\n{msg}")

    def _slider_released(self) -> None:
        self._seeking = False
        self.player.setPosition(self.slider.value())

    def _skip(self, delta: int) -> None:
        pos = max(0, min(self.player.position() + delta, max(self.duration_ms - 100, 0)))
        self.player.setPosition(pos)

    # --- 내보내기 ---
    def _export_menu(self) -> None:
        if not self.rec:
            return
        m = QMenu(self.widget)
        done = bool(self.segments)
        for label, fn, enabled in (
            ("텍스트 파일 (.txt)", self._export_txt, done),
            ("자막 파일 (.srt)", self._export_srt, done),
            ("텍스트 복사 (클립보드)", self._copy_text, done),
            (None, None, None),
            ("음성 파일 (.wav)", self._export_wav, self.rec.file_path.exists()),
        ):
            if label is None:
                m.addSeparator()
                continue
            a = m.addAction(label)
            a.setEnabled(enabled)
            a.triggered.connect(fn)
        m.exec(self.export_btn.mapToGlobal(QPoint(0, -m.sizeHint().height() - 4)))

    def _ask_path(self, ext: str, filt: str) -> Path | None:
        default_dir = self.ctx.db.get_setting("export_dir") or str(Path.home() / "Documents")
        name = f"{_safe_filename(self.rec.title)}.{ext}"
        path, _ = QFileDialog.getSaveFileName(self.widget, "내보내기", str(Path(default_dir) / name), filt)
        if not path:
            return None
        self.ctx.db.set_setting("export_dir", str(Path(path).parent))
        return Path(path)

    def _write(self, path: Path, content: str) -> None:
        try:
            path.write_text(content, encoding="utf-8-sig")
        except OSError as e:
            QMessageBox.warning(self.widget, "내보내기 실패", str(e))

    def _export_txt(self) -> None:
        if p := self._ask_path("txt", "텍스트 파일 (*.txt)"):
            self._write(p, to_txt(self.rec, self.segments))

    def _export_srt(self) -> None:
        if p := self._ask_path("srt", "자막 파일 (*.srt)"):
            self._write(p, to_srt(self.segments))

    def _copy_text(self) -> None:
        QGuiApplication.clipboard().setText(to_txt(self.rec, self.segments))
        self.ctx.toast("텍스트를 클립보드에 복사했습니다.")

    def _export_wav(self) -> None:
        if p := self._ask_path("wav", "WAV 음성 파일 (*.wav)"):
            try:
                shutil.copyfile(self.rec.file_path, p)
            except OSError as e:
                QMessageBox.warning(self.widget, "내보내기 실패", str(e))
