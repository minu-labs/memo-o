import re
from pathlib import Path

import pytest

from memo_o import i18n
from memo_o.i18n import UI_LANGS, _STRINGS, tr
from memo_o.stt import SPEECH_LANGUAGES, language_options

SRC = Path(__file__).resolve().parent.parent / "memo_o"


@pytest.fixture(autouse=True)
def _restore_lang():
    prev = i18n.language()
    yield
    i18n.set_language(prev)


def test_every_string_has_all_languages():
    for key, values in _STRINGS.items():
        assert set(values) == set(UI_LANGS), key
        assert all(v.strip() for v in values.values()), key


def test_placeholders_match_between_languages():
    for key, values in _STRINGS.items():
        fields = {lang: set(re.findall(r"\{(\w+)\}", v)) for lang, v in values.items()}
        assert len(set(map(frozenset, fields.values()))) == 1, key


def test_all_keys_used_in_source_exist():
    used = set()
    for p in SRC.rglob("*.py"):
        used |= set(re.findall(r"""\btr\(\s*["']([\w.]+)["']""", p.read_text(encoding="utf-8")))
    assert used, "tr() 호출을 찾지 못함"
    assert used - set(_STRINGS) == set()


def test_tr_switches_language_and_formats():
    i18n.set_language("ko")
    assert tr("rec.default_title", date="09-23 10:00") == "녹음 09-23 10:00"
    i18n.set_language("en")
    assert tr("rec.default_title", date="09-23 10:00") == "Recording 09-23 10:00"
    # 값 안의 중괄호는 그대로 둔다 (제목에 {}가 있어도 안전)
    assert tr("del.confirm", title="a{b}").startswith("Delete 'a{b}'")


def test_resolve_and_unknown_language():
    assert i18n.resolve("ko") == "ko"
    assert i18n.resolve("en") == "en"
    assert i18n.resolve("auto") in UI_LANGS
    assert i18n.resolve(None) in UI_LANGS
    i18n.set_language("xx")
    assert i18n.language() == "en"


def test_speech_language_options():
    assert language_options("auto") == {"language": None, "multilingual": True}
    assert language_options(None) == {"language": None, "multilingual": True}
    assert language_options("ko") == {"language": "ko", "multilingual": False}
    assert language_options("vi") == {"language": "vi", "multilingual": False}
    assert "ko" in SPEECH_LANGUAGES and "en" in SPEECH_LANGUAGES
