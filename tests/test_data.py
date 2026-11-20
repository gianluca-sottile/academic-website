import shutil
import pytest
from conftest import FIXTURES
import data


def test_i18n_fallback():
    assert data.tr({"en": "Hi"}, "it") == ("Hi", "en")
    assert data.tr("Ciao", "en").text == "Ciao"
    assert data.tr({"en": "a", "it": "b"}, "it") == ("b", "it")
    assert data.tr(None, "en") == ("", "en")


def test_load_all_fixture():
    d = data.load_all(FIXTURES / "data")
    assert d.profile["name"] == "Test Person"
    assert d.talks[0]["id"] == "t1"
    assert d.publications == []
    assert data.validate(d) == []


def _copy(tmp_path):
    dst = tmp_path / "data"
    shutil.copytree(FIXTURES / "data", dst)
    return dst


def test_validate_missing_required(tmp_path):
    dd = _copy(tmp_path)
    (dd / "talks.yml").write_text("- id: t9\n  title: x\n  event: e\n  place: p\n  kind: talk\n")
    errs = data.validate(data.load_all(dd))
    assert any("talks.yml" in e and "t9" in e and "date" in e for e in errs)


def test_duplicate_ids(tmp_path):
    dd = _copy(tmp_path)
    (dd / "news.yml").write_text("- {id: a, date: 2024-01-01, text: x}\n- {id: a, date: 2024-01-02, text: y}\n")
    errs = data.validate(data.load_all(dd))
    assert any("duplicate id 'a'" in e for e in errs)


@pytest.mark.parametrize("bad", ["https://anonymous.4open.science/r/X", "IS-Score paper", "MERE-D-26-02012", "Lorenz curve comment"])
def test_forbidden_content(tmp_path, bad):
    dd = _copy(tmp_path)
    (dd / "news.yml").write_text(f"- id: z\n  date: 2024-01-01\n  text: \"{bad}\"\n")
    errs = data.validate(data.load_all(dd))
    assert any("forbidden" in e for e in errs)


def test_empty_section_ok(tmp_path):
    dd = _copy(tmp_path)
    (dd / "news.yml").write_text("")
    d = data.load_all(dd)
    assert d.news == []
    assert data.validate(d) == []


def test_drafts_listed(tmp_path):
    dd = _copy(tmp_path)
    (dd / "news.yml").write_text("- {id: d1, date: 2024-01-01, text: x, draft: true}\n")
    assert data.drafts(data.load_all(dd)) == ["news.yml: d1"]


def test_unknown_theme_in_publication(tmp_path):
    dd = _copy(tmp_path)
    (dd / "publications.json").write_text('{"items": [{"id": "10.1/x", "title": "T", "year": 2020, "type": "article", "themes": ["nope"]}]}')
    errs = data.validate(data.load_all(dd))
    assert any("unknown theme 'nope'" in e for e in errs)


def test_broken_localized_mapping(tmp_path):
    dd = _copy(tmp_path)
    (dd / "news.yml").write_text("- {id: z, date: 2024-01-01, text: {en: A, B, it: C}}\n")
    errs = data.validate(data.load_all(dd))
    assert any("unquoted comma" in e for e in errs)
