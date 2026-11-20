import re
from pathlib import Path
import pytest
import build

PAGES = ("publications", "teaching", "projects", "software", "talks", "cv")


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("s") / "site"
    build.build(build.ROOT / "data", out)
    return out


@pytest.mark.parametrize("page", PAGES)
@pytest.mark.parametrize("lang", ("en", "it"))
def test_all_pages_both_langs(site, page, lang):
    p = site / (page if lang == "en" else f"it/{page}") / "index.html"
    assert p.exists()
    assert f'<html lang="{lang}"' in p.read_text()


def test_switcher_targets_same_page(site):
    html = (site / "publications" / "index.html").read_text()
    assert re.search(r'class="lang-switch" href="/it/publications/"', html)
    html_it = (site / "it" / "teaching" / "index.html").read_text()
    assert re.search(r'class="lang-switch" href="/teaching/"', html_it)


def test_pubs_page_works_without_js(site):
    import json
    n = len(json.loads((build.ROOT / "data" / "publications.json").read_text())["items"])
    html = (site / "publications" / "index.html").read_text()
    assert html.count('class="pub"') == n


def test_redirects(site):
    rules = (site / "_redirects").read_text()
    for pat in ("/publication/*", "/talk/*", "/courses/*", "/project/*", "/post/*", "/talk2/*"):
        assert re.search(rf"^{re.escape(pat)}\s+\S+\s+301", rules, re.M), pat
    assert re.search(r"^/CV_gianluca_sottile\.pdf\s+/files/CV_gianluca_sottile\.pdf\s+301", rules, re.M)
    assert re.search(r"^/SIS2019_PresentazioneSottile\.pdf\s+/files/SIS2019_PresentazioneSottile\.pdf\s+301", rules, re.M)


def test_internal_links_resolve(site):
    bad = []
    for f in site.rglob("*.html"):
        for href in re.findall(r'href="(/[^"#?]*)', f.read_text()):
            target = site / href.lstrip("/")
            if href.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                bad.append(f"{f.relative_to(site)} -> {href}")
    assert not bad, bad[:10]
