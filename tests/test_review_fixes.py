import json, re, shutil
import pytest
from conftest import FIXTURES
import build, data
import fetch_publications as fp


def _copy_real(tmp_path):
    dd = tmp_path / "data"
    shutil.copytree(build.ROOT / "data", dd)
    return dd


def test_production_hides_links_to_missing_sections_and_zero_counters(tmp_path, monkeypatch):
    monkeypatch.setenv("BUILD_ENV", "production")
    dd = _copy_real(tmp_path)
    import yaml
    sw = yaml.safe_load((dd / "software.yml").read_text())
    for item in sw:
        item["draft"] = True
    (dd / "software.yml").write_text(yaml.safe_dump(sw, allow_unicode=True))
    out = tmp_path / "site"
    build.build(dd, out)
    html = (out / "index.html").read_text()
    assert 'href="#software"' not in html and 'href="/#software"' not in html
    assert 'data-count="pkgs">0<' not in html


def test_production_fails_while_profile_is_draft(tmp_path, monkeypatch):
    monkeypatch.setenv("BUILD_ENV", "production")
    dd = _copy_real(tmp_path)
    (dd / "profile.yml").write_text((dd / "profile.yml").read_text() + "draft: true\n")
    with pytest.raises(build.ValidationError):
        build.build(dd, tmp_path / "site")


def test_shrink_guard_keeps_previous(tmp_path):
    out = tmp_path / "p.json"
    out.write_text(json.dumps({"items": [{"id": str(i), "title": f"t{i}"} for i in range(10)]}))
    before = out.read_bytes()
    assert fp.write_if_changed(out, [{"id": "1", "title": "t1"}]) is False
    assert out.read_bytes() == before


def _w(doi, title, typ="article", cites=0):
    return {"doi": doi and f"https://doi.org/{doi}", "title": title, "publication_year": 2020, "type": typ, "cited_by_count": cites, "authorships": []}


def test_dedupe_by_doi_first():
    items = fp.process([_w("10.1/a", "Same title"), _w("10.1/b", "Same title", "conference-paper")], {}, [])
    assert {i["id"] for i in items} == {"10.1/a", "10.1/b"}
    items = fp.process([_w("10.1/a", "Title one"), _w("10.1/A", "Title one (corrected)")], {}, [])
    assert len(items) == 1
    items = fp.process([_w(None, "Some paper", "book-chapter"), _w("10.1/c", "Some paper")], {}, [])
    assert [i["id"] for i in items] == ["10.1/c"]


def test_unsafe_urls_dropped():
    w = _w(None, "Evil", "article")
    w["primary_location"] = {"landing_page_url": "javascript:alert(1)"}
    w["open_access"] = {"oa_url": "javascript:alert(2)"}
    p = fp.normalize(w)
    assert p["url"] == "" and p["oa_url"] is None
    assert build.safe_url("javascript:alert(1)") == "" and build.safe_url("/files/x.pdf") == "/files/x.pdf"
    assert build.safe_url("https://a.b") == "https://a.b" and build.safe_url("mailto:x@y.z") == "mailto:x@y.z"


def test_exclude_titles_override():
    items = fp.process([_w("10.6/x", "Gaussian Graphical Models for Partially Observed Multivariate Functional Data")],
                       {"exclude_titles": ["Partially Observed Multivariate Functional"]}, [])
    assert items == []


def test_real_overrides_exclude_in_progress_work():
    import yaml
    ov = yaml.safe_load((build.ROOT / "data" / "publications.overrides.yml").read_text())
    pats = " ".join(ov.get("exclude_titles", []))
    assert "Partially Observed Multivariate Functional" in pats


def test_hero_svg_links_are_accessible(tmp_path):
    build.build(build.ROOT / "data", tmp_path / "site")
    html = (tmp_path / "site" / "index.html").read_text()
    svg = re.search(r'<svg viewBox="-8 0 840 440"[^>]*>', html).group(0)
    assert 'role="img"' not in svg and 'aria-label' in svg


def test_fallback_title_has_badge_and_lang(tmp_path):
    dd = _copy_real(tmp_path)
    (dd / "talks.yml").write_text("- {id: x, date: 2020-01-01, title: {en: Only English title}, event: E, place: P, kind: talk}\n")
    build.build(dd, tmp_path / "site")
    html = (tmp_path / "site" / "it" / "talks" / "index.html").read_text()
    assert re.search(r'<span lang="en">Only English title</span><span class="lang-badge"', html)


def test_no_doi_no_url_does_not_link_to_none(tmp_path):
    dd = _copy_real(tmp_path)
    pubs = json.loads((dd / "publications.json").read_text())
    pubs["items"].append({"id": "manual", "doi": None, "url": "", "title": "Manual", "year": 2000, "type": "article", "authors": [], "themes": [], "links": []})
    (dd / "publications.json").write_text(json.dumps(pubs))
    build.build(dd, tmp_path / "site")
    assert "doi.org/None" not in (tmp_path / "site" / "publications" / "index.html").read_text()


def test_forbidden_code_names(tmp_path):
    dd = tmp_path / "d"
    shutil.copytree(FIXTURES / "data", dd)
    (dd / "news.yml").write_text("- {id: z, date: 2024-01-01, text: FCST submitted}\n")
    assert any("forbidden" in e for e in data.validate(data.load_all(dd)))
