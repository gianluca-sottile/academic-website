from pathlib import Path
from conftest import FIXTURES
import build


def test_build_writes_both_languages(tmp_path):
    out = tmp_path / "site"
    build.build(FIXTURES / "data", out)
    en = (out / "index.html").read_text()
    it = (out / "it" / "index.html").read_text()
    for html in (en, it):
        assert 'hreflang="it"' in html
        assert 'hreflang="en"' in html
        assert 'hreflang="x-default"' in html
    assert '<html lang="en"' in en
    assert '<html lang="it"' in it


def test_url_for():
    assert build.url_for("publications", "it") == "/it/publications/"
    assert build.url_for("index", "en") == "/"
    assert build.url_for("index", "it") == "/it/"


def test_build_fails_on_invalid_data(tmp_path):
    import shutil, pytest
    dd = tmp_path / "data"
    shutil.copytree(FIXTURES / "data", dd)
    (dd / "news.yml").write_text("- {id: x, text: no date}\n")
    with pytest.raises(build.ValidationError):
        build.build(dd, tmp_path / "site")


def _build_real(tmp_path, env=None, monkeypatch=None):
    out = tmp_path / "site"
    build.build(build.ROOT / "data", out)
    return out


def test_empty_section_hidden(tmp_path):
    import shutil
    dd = tmp_path / "data"
    shutil.copytree(FIXTURES / "data", dd)
    (dd / "news.yml").write_text("")
    out = tmp_path / "site"
    build.build(dd, out)
    html = (out / "index.html").read_text()
    assert 'id="news"' not in html and 'id="projects"' not in html


def test_counters_match_data(tmp_path):
    import json, re
    out = _build_real(tmp_path)
    html = (out / "index.html").read_text()
    pubs = json.loads((build.ROOT / "data" / "publications.json").read_text())["items"]
    assert re.search(r'data-count="pubs">%d<' % len(pubs), html)
    assert re.search(r'data-count="cites">%d<' % sum(p.get("citations") or 0 for p in pubs), html)
    assert 'data-count="pkgs">4<' in html


def test_no_draft_in_production(tmp_path, monkeypatch, capsys):
    import shutil
    monkeypatch.setenv("BUILD_ENV", "production")
    dd = tmp_path / "data"
    shutil.copytree(build.ROOT / "data", dd)
    proj = (dd / "projects.yml").read_text().replace("- id: statatlas\n", "- id: statatlas\n  draft: true\n")
    (dd / "projects.yml").write_text(proj)
    out = tmp_path / "site"
    build.build(dd, out)
    html = (out / "index.html").read_text()
    assert "StatAtlas" not in html          # draft project hidden
    assert "From Data to Models with R" in html  # approved project shown
    assert "draft item" in capsys.readouterr().err


def test_no_external_runtime_fetch():
    js = (build.ROOT / "src" / "assets" / "js" / "site.js").read_text()
    assert "fetch(" not in js and "XMLHttpRequest" not in js


def test_hero_paths_distinct_ends():
    ends = [p["end_y"] for p in build.hero_paths()]
    assert len(set(ends)) == len(ends) and all(abs(e - 210) > 10 for e in ends)
    assert min(b - a for a, b in zip(sorted(ends), sorted(ends)[1:])) >= 30
