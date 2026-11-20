import json
import responses
from conftest import FIXTURES
import fetch_publications as fp

PAGE = json.loads((FIXTURES / "openalex_page.json").read_text())
THEMES = [{"id": "sparse", "openalex_keywords": ["lasso", "sparse"]},
          {"id": "graphical", "openalex_keywords": ["graphical"]}]


def _items():
    return fp.process(PAGE["results"], {}, THEMES)


def test_parses_openalex():
    items = _items()
    isl = next(i for i in items if i["id"] == "10.1177/0962280219842890")
    assert isl["venue"] == "Statistical Methods in Medical Research"
    assert isl["authors"] == ["Giovanna Cilluffo", "Gianluca Sottile"]
    assert isl["year"] == 2019 and isl["citations"] == 36 and isl["type"] == "article"
    assert isl["url"] == "https://doi.org/10.1177/0962280219842890"


def test_excludes_unpublished_and_non_papers():
    ids = {i["id"] for i in _items()}
    assert "10.32614/cran.package.islasso" not in ids
    assert "10.6084/m9.figshare.5598133" not in ids
    assert "10.1234/arxiv-like" not in ids
    assert "10.5194/egusphere-egu2020-18518" not in ids


def test_dedupe_doi_and_preprint():
    items = _items()
    titles = [fp.norm_title(i["title"]) for i in items]
    assert len(titles) == len(set(titles))
    assert sum("induced smoothed lasso" in t for t in titles) == 1


def test_title_sanitising():
    t = next(i for i in _items() if "new" in i["title"])
    assert t["title"] == "A new approach & test with $\\ell_1$"


def test_no_doi_kept():
    t = next(i for i in _items() if "new" in i["title"])
    assert t["doi"] is None and t["id"].startswith("oa-") and t["type"] == "chapter"


def test_theme_suggestion():
    isl = next(i for i in _items() if i["id"] == "10.1177/0962280219842890")
    assert isl["themes"] == ["sparse"]
    fg = next(i for i in _items() if i["id"] == "10.1093/jrsssc/qlaf042")
    assert fg["themes"] == ["graphical"]
    assert fg["oa_url"] == "https://oa.example/x.pdf"


def test_overrides_apply():
    ov = {"hide": ["10.1093/jrsssc/qlaf042"], "selected": ["10.1177/0962280219842890"],
          "themes": {"10.1177/0962280219842890": ["graphical"]},
          "links": {"10.1177/0962280219842890": [{"label": "R package", "url": "https://github.com/gianluca-sottile/islasso"}]},
          "extra": [{"id": "manual-1", "title": "Manual entry", "authors": ["G. Sottile"], "year": 2026, "type": "article", "venue": "J"}]}
    items = fp.process(PAGE["results"], ov, THEMES)
    ids = [i["id"] for i in items]
    assert "10.1093/jrsssc/qlaf042" not in ids and "manual-1" in ids
    isl = next(i for i in items if i["id"] == "10.1177/0962280219842890")
    assert isl["selected"] is True and isl["themes"] == ["graphical"] and isl["links"][0]["label"] == "R package"
    assert next(i for i in items if i["id"] == "manual-1")["selected"] is False


def test_sorted_year_desc_then_title():
    items = _items()
    keys = [(-i["year"], i["title"].lower()) for i in items]
    assert keys == sorted(keys)


@responses.activate
def test_fetch_failure_keeps_previous(tmp_path):
    out = tmp_path / "publications.json"
    out.write_text('{"items": [{"id": "keep"}]}')
    before = out.read_bytes()
    responses.add(responses.GET, fp.OPENALEX_URL, status=503)
    rc = fp.main(["--out", str(out), "--overrides", str(tmp_path / "none.yml"), "--profile", str(FIXTURES / "data" / "profile.yml"), "--retries", "1"])
    assert rc == 0 and out.read_bytes() == before


@responses.activate
def test_fetch_paginates_and_writes(tmp_path):
    page1 = {"meta": {"next_cursor": "abc"}, "results": PAGE["results"][:4]}
    page2 = {"meta": {"next_cursor": None}, "results": PAGE["results"][4:]}
    responses.add(responses.GET, fp.OPENALEX_URL, json=page1)
    responses.add(responses.GET, fp.OPENALEX_URL, json=page2)
    out = tmp_path / "publications.json"
    rc = fp.main(["--out", str(out), "--overrides", str(tmp_path / "none.yml"), "--profile", str(FIXTURES / "data" / "profile.yml")])
    data = json.loads(out.read_text())
    assert rc == 0 and len(data["items"]) == 4 and data["source"] == "OpenAlex (ORCID 0000-0001-9347-7251)"


def test_unchanged_content_not_rewritten(tmp_path):
    out = tmp_path / "p.json"
    items = _items()
    assert fp.write_if_changed(out, items) is True
    mtime = out.read_text()
    assert fp.write_if_changed(out, items) is False
    assert out.read_text() == mtime


def test_repository_source_is_not_a_venue():
    w = {"doi": None, "title": "Tuning parameter selection in LASSO regression", "publication_year": 2016, "type": "book-chapter",
         "primary_location": {"landing_page_url": "http://hdl.handle.net/10447/221666",
                              "source": {"display_name": "Nova Science Publishers (Nova Science Publishers, Inc.)", "type": "repository"}},
         "authorships": []}
    p = fp.normalize(w)
    assert p["venue"] == "" and p["url"] == "http://hdl.handle.net/10447/221666"


def test_latex_subscript_in_title():
    assert fp.clean_title("Registered OD$$_{600}$$ Growth-Curve") == "Registered OD₆₀₀ Growth-Curve"


def test_ebook_platform_uses_series_name():
    w = {"doi": "https://doi.org/10.1007/978-3-031-96736-8_75", "title": "Sparse Multiple Gaussian Graphical Models", "publication_year": 2025,
         "type": "conference-paper", "authorships": [],
         "primary_location": {"raw_source_name": "Italian Statistical Society Series on Advances in Statistics",
                              "source": {"display_name": "Springer eBooks", "type": "ebook platform"}}}
    assert fp.normalize(w)["venue"] == "Italian Statistical Society Series on Advances in Statistics"
