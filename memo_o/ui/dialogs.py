import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QTextBrowser, QVBoxLayout,
)

from .. import __version__
from ..paths import data_dir, resource_dir
from ..stt import MODEL_SIZES, available_models

LEGAL_NOTICE = (
    "<b>녹음 관련 법적 고지</b><br>"
    "통신비밀보호법에 따라 <b>본인이 참여한 대화</b>의 녹음은 상대방의 동의 없이도 가능하지만, "
    "<b>본인이 참여하지 않은 타인 간의 대화를 몰래 녹음하는 것은 불법</b>이며 형사처벌 대상입니다. "
    "녹음 기능의 사용과 그 결과에 대한 책임은 사용자에게 있습니다."
)

PRIVACY_NOTICE = (
    "<b>개인정보 보호</b><br>"
    "MemoO는 인터넷에 연결하지 않습니다. 녹음 파일과 변환된 텍스트는 "
    "이 PC 안에서만 처리·저장되며 외부 서버로 전송되지 않습니다."
)


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
    d, lay = _base(parent, "MemoO 사용 안내")
    lay.addWidget(_para("MemoO에 오신 것을 환영합니다. 사용 전에 아래 내용을 확인해주세요."))
    lay.addWidget(_para(LEGAL_NOTICE))
    lay.addWidget(_para(PRIVACY_NOTICE))
    agree = QCheckBox("위 내용을 확인했습니다")
    ok = QPushButton("시작하기")
    ok.setObjectName("Primary")
    ok.setEnabled(False)
    agree.toggled.connect(ok.setEnabled)
    ok.clicked.connect(d.accept)
    lay.addWidget(agree)
    lay.addWidget(ok, 0, Qt.AlignRight)
    d.setWindowFlag(Qt.WindowCloseButtonHint, False)
    return d.exec() == QDialog.Accepted


def about_dialog(parent) -> None:
    d, lay = _base(parent, "MemoO 정보", 400)
    lay.addWidget(_para(f"<span style='font-size:16px; font-weight:600'>MemoO</span> &nbsp;v{__version__}<br>"
                        "오프라인 녹음 + 텍스트 변환(STT) 프로그램 · 무료"))
    lay.addWidget(_para(PRIVACY_NOTICE))
    lay.addWidget(_para(LEGAL_NOTICE))
    lay.addWidget(_para("<b>오픈소스 라이선스</b>"))
    view = QTextBrowser()
    view.setMinimumHeight(160)
    view.setStyleSheet("font-size: 11px; background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 6px;")
    notices = resource_dir() / "THIRD_PARTY_NOTICES.txt"
    view.setPlainText(notices.read_text(encoding="utf-8") if notices.exists() else "")
    lay.addWidget(view, 1)
    bb = QDialogButtonBox(QDialogButtonBox.Close)
    bb.rejected.connect(d.reject)
    lay.addWidget(bb)
    d.resize(420, 560)
    d.exec()


def settings_dialog(parent, db, stt_device: str) -> bool:
    """변환 모델 선택. 변경되면 True."""
    d, lay = _base(parent, "설정")
    current = db.get_setting("model", "small")
    models = available_models()

    lay.addWidget(_para("<b>텍스트 변환 모델</b>"))
    group = QButtonGroup(d)
    desc = {
        "small": "small — 빠름, 일반 PC 권장",
        "medium": "medium — 더 정확함, 느림 (고사양 PC 권장)",
    }
    for size in MODEL_SIZES:
        rb = QRadioButton(desc[size] + ("" if size in models else "  (모델 없음)"))
        rb.setEnabled(size in models)
        rb.setChecked(size == current)
        rb.setProperty("size", size)
        group.addButton(rb)
        lay.addWidget(rb)

    user_models = data_dir() / "models"
    lay.addWidget(_para(
        f"<span style='color:#616161'>medium 모델은 용량이 커서 기본 설치에 포함되지 않습니다. "
        f"다운로드 페이지에서 받은 모델 폴더(medium)를 아래 위치에 넣으면 선택할 수 있습니다.<br>"
        f"{user_models}<br><br>"
        f"변환 장치: {'GPU (CUDA)' if stt_device == 'cuda' else 'CPU'}</span>"
    ))
    open_btn = QPushButton("모델 폴더 열기")
    open_btn.clicked.connect(lambda: os.startfile(user_models))
    row = QHBoxLayout()
    row.addWidget(open_btn)
    row.addStretch(1)
    lay.addLayout(row)

    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.button(QDialogButtonBox.Ok).setText("저장")
    bb.button(QDialogButtonBox.Cancel).setText("취소")
    bb.accepted.connect(d.accept)
    bb.rejected.connect(d.reject)
    lay.addWidget(bb)
    if d.exec() != QDialog.Accepted:
        return False
    checked = group.checkedButton()
    if checked is None:
        return False
    size = checked.property("size")
    if size != current:
        db.set_setting("model", size)
        return True
    return False
