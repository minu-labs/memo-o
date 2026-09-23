import os
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QTextBrowser, QVBoxLayout,
)

from .. import __version__, i18n
from ..i18n import UI_LANG_NAMES, tr
from ..paths import data_dir, resource_dir
from ..stt import DEFAULT_SPEECH_LANG, MODEL_SIZES, SPEECH_LANGUAGES, available_models
from . import theme


def _base(parent, title: str, width: int = 380) -> tuple[QDialog, QVBoxLayout]:
    d = QDialog(parent)
    d.setWindowTitle(title)
    d.setMinimumWidth(width)
    lay = QVBoxLayout(d)
    lay.setContentsMargins(20, 18, 20, 16)
    lay.setSpacing(12)
    return d, lay


def _para(html: str) -> QLabel:
    lbl = QLabel(html)
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.RichText)
    lbl.setStyleSheet("font-size: 12px; line-height: 150%;")
    return lbl


def first_run_notice(parent) -> bool:
    d, lay = _base(parent, tr("notice.title"))
    lay.addWidget(_para(tr("notice.welcome")))
    lay.addWidget(_para(tr("notice.legal")))
    lay.addWidget(_para(tr("notice.privacy")))
    agree = QCheckBox(tr("notice.agree"))
    ok = QPushButton(tr("notice.start"))
    ok.setObjectName("Primary")
    ok.setEnabled(False)
    agree.toggled.connect(ok.setEnabled)
    ok.clicked.connect(d.accept)
    lay.addWidget(agree)
    lay.addWidget(ok, 0, Qt.AlignRight)
    d.setWindowFlag(Qt.WindowCloseButtonHint, False)
    return d.exec() == QDialog.Accepted


def about_dialog(parent) -> None:
    d, lay = _base(parent, tr("menu.about"), 400)
    lay.addWidget(_para(f"<span style='font-size:16px; font-weight:600'>MemoO</span> &nbsp;v{__version__}<br>"
                        f"{tr('about.tagline')}"))
    lay.addWidget(_para(tr("notice.privacy")))
    lay.addWidget(_para(tr("notice.legal")))
    lay.addWidget(_para(tr("about.licenses")))
    view = QTextBrowser()
    view.setMinimumHeight(160)
    view.setStyleSheet(
        f"font-size: 11px; background: {theme.CARD}; color: {theme.TEXT}; "
        f"border: 1px solid {theme.BORDER}; border-radius: 6px;"
    )
    notices = resource_dir() / "THIRD_PARTY_NOTICES.txt"
    view.setPlainText(notices.read_text(encoding="utf-8") if notices.exists() else "")
    lay.addWidget(view, 1)
    bb = QDialogButtonBox(QDialogButtonBox.Close)
    bb.rejected.connect(d.reject)
    lay.addWidget(bb)
    d.resize(420, 560)
    d.exec()


@dataclass
class SettingsChanges:
    stt: bool = False            # 모델/음성 언어 변경 → 다음 변환부터 적용
    theme: str | None = None     # 바뀐 테마
    ui_lang: bool = False        # 화면 언어 변경 → 재시작 후 적용


def _lang_combo(items: list[tuple[str, str]], current: str) -> QComboBox:
    combo = QComboBox()
    for code, label in items:
        combo.addItem(label, code)
    combo.setCurrentIndex(max(combo.findData(current), 0))
    return combo


def settings_dialog(parent, db, stt_device: str) -> SettingsChanges:
    """화면 언어/음성 언어/모델/테마 선택. 바뀐 항목을 반환한다."""
    changes = SettingsChanges()
    d, lay = _base(parent, tr("menu.settings"))

    lay.addWidget(_para(tr("settings.ui_lang")))
    current_ui = db.get_setting("ui_lang", "auto")
    ui_combo = _lang_combo([("auto", tr("settings.ui_auto")), *UI_LANG_NAMES.items()], current_ui)
    lay.addWidget(ui_combo)

    lay.addWidget(_para(tr("settings.speech_lang")))
    current_speech = db.get_setting("stt_lang", DEFAULT_SPEECH_LANG)
    speech_combo = _lang_combo([("auto", tr("settings.speech_auto")), *SPEECH_LANGUAGES.items()],
                               current_speech)
    speech_combo.setMaxVisibleItems(12)
    lay.addWidget(speech_combo)
    lay.addWidget(_para(f"<span style='color:{theme.TEXT_SUB}'>{tr('settings.speech_help')}</span>"))

    current = db.get_setting("model", "small")
    models = available_models()

    lay.addWidget(_para(tr("settings.model")))
    group = QButtonGroup(d)
    desc = {"small": tr("settings.model_small"), "medium": tr("settings.model_medium")}
    for size in MODEL_SIZES:
        rb = QRadioButton(desc[size] + ("" if size in models else tr("settings.model_missing")))
        rb.setEnabled(size in models)
        rb.setChecked(size == current)
        rb.setProperty("modelSize", size)
        group.addButton(rb)
        lay.addWidget(rb)

    user_models = data_dir() / "models"
    device = "GPU (CUDA)" if stt_device == "cuda" else "CPU"
    lay.addWidget(_para(
        f"<span style='color:{theme.TEXT_SUB}'>{tr('settings.model_help', path=user_models, device=device)}</span>"
    ))
    open_btn = QPushButton(tr("settings.open_models"))
    open_btn.clicked.connect(lambda: os.startfile(user_models))
    row = QHBoxLayout()
    row.addWidget(open_btn)
    row.addStretch(1)
    lay.addLayout(row)

    lay.addWidget(_para(tr("settings.theme")))
    current_theme = db.get_setting("theme", "light")
    theme_group = QButtonGroup(d)
    theme_desc = {"light": tr("settings.theme_light"), "dark": tr("settings.theme_dark")}
    for mode in ("light", "dark"):
        rb = QRadioButton(theme_desc[mode])
        rb.setChecked(mode == current_theme)
        rb.setProperty("themeMode", mode)
        theme_group.addButton(rb)
        lay.addWidget(rb)

    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.button(QDialogButtonBox.Ok).setText(tr("common.save"))
    bb.button(QDialogButtonBox.Cancel).setText(tr("common.cancel"))
    bb.accepted.connect(d.accept)
    bb.rejected.connect(d.reject)
    lay.addWidget(bb)
    if d.exec() != QDialog.Accepted:
        return changes

    ui_lang = ui_combo.currentData()
    if ui_lang != current_ui:
        db.set_setting("ui_lang", ui_lang)
        changes.ui_lang = i18n.resolve(ui_lang) != i18n.language()

    speech = speech_combo.currentData()
    if speech != current_speech:
        db.set_setting("stt_lang", speech)
        changes.stt = True

    theme_checked = theme_group.checkedButton()
    if theme_checked is not None and theme_checked.property("themeMode") != current_theme:
        changes.theme = theme_checked.property("themeMode")
        db.set_setting("theme", changes.theme)

    checked = group.checkedButton()
    if checked is not None and checked.property("modelSize") != current:
        db.set_setting("model", checked.property("modelSize"))
        changes.stt = True
    return changes
