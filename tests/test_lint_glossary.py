"""lint.py enforces glossary.md: a JP term needs its EN form, Avoid spellings fail."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import lint  # noqa: E402

GLOSSARY = """
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| オルグ | Org(s) | | | Orug |
| ガオレンジャー | GaoRanger(s) | | | Gaorangers |
| オルグはんのう / はんのう | Org reading / reading | | | reaction |
"""


def errs(jp, en, tmp_path):
    g = tmp_path / "g.md"
    g.write_text(GLOSSARY, encoding="utf-8")
    return lint.glossary_errors("x", jp, en, lint.load_glossary(g))


def test_pass(tmp_path):
    assert errs("オルグがあらわれた", "The Orgs appeared", tmp_path) == []
    assert errs("ガオレンジャーの", "GaoRanger save file", tmp_path) == []
    assert errs("またオルグはんのうよ", "Another Org reading!", tmp_path) == []


def test_missing_term_fails(tmp_path):
    assert errs("オルグがあらわれた", "The monsters appeared", tmp_path)


def test_avoid_fails(tmp_path):
    assert errs("ガオレンジャー", "Gaorangers!", tmp_path)


def test_katakana_run_is_whole(tmp_path):
    # オルグ inside a longer katakana word is not the term
    assert errs("デュークオルグ", "Duke", tmp_path) == []


def test_real_glossary_parses():
    assert len(lint.load_glossary()) >= 10
