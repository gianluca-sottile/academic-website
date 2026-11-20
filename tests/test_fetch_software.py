import json
import responses
import fetch_software as fs

PKGS = [{"id": "islasso", "name": "islasso", "repo": "gianluca-sottile/islasso", "cran": "islasso"},
        {"id": "nocran", "name": "nocran", "repo": "gianluca-sottile/nocran"}]


def _mock_all():
    responses.add(responses.GET, fs.CRANDB.format(pkg="islasso"), json={"Version": "1.6.0", "Date/Publication": "2025-03-01 10:00:00 UTC"})
    responses.add(responses.GET, fs.CRANLOGS.format(pkg="islasso"), json=[{"downloads": 812, "package": "islasso"}])
    responses.add(responses.GET, fs.GITHUB.format(repo="gianluca-sottile/islasso"), json={"stargazers_count": 4, "html_url": "https://github.com/gianluca-sottile/islasso"})
    responses.add(responses.GET, fs.GITHUB.format(repo="gianluca-sottile/nocran"), json={"stargazers_count": 1, "html_url": "https://github.com/gianluca-sottile/nocran"})


@responses.activate
def test_parses_sources():
    _mock_all()
    meta = fs.collect(PKGS, {}, fs.session())
    assert meta["islasso"] == {"cran_version": "1.6.0", "cran_published": "2025-03-01", "downloads_last_month": 812,
                               "gh_stars": 4, "gh_url": "https://github.com/gianluca-sottile/islasso"}
    assert meta["nocran"]["cran_version"] is None and meta["nocran"]["gh_stars"] == 1


@responses.activate
def test_partial_failure_keeps_old_fields():
    responses.add(responses.GET, fs.CRANDB.format(pkg="islasso"), status=500)
    responses.add(responses.GET, fs.CRANLOGS.format(pkg="islasso"), status=500)
    responses.add(responses.GET, fs.GITHUB.format(repo="gianluca-sottile/islasso"), json={"stargazers_count": 5, "html_url": "u"})
    old = {"islasso": {"cran_version": "1.5.0", "cran_published": "2024-01-01", "downloads_last_month": 700, "gh_stars": 3, "gh_url": "u"}}
    meta = fs.collect(PKGS[:1], old, fs.session())
    assert meta["islasso"]["cran_version"] == "1.5.0" and meta["islasso"]["downloads_last_month"] == 700
    assert meta["islasso"]["gh_stars"] == 5


@responses.activate
def test_main_writes_json(tmp_path):
    _mock_all()
    yml = tmp_path / "software.yml"
    yml.write_text("- {id: islasso, name: islasso, repo: gianluca-sottile/islasso, cran: islasso}\n")
    out = tmp_path / "software.json"
    assert fs.main(["--packages", str(yml), "--out", str(out)]) == 0
    assert json.loads(out.read_text())["islasso"]["cran_version"] == "1.6.0"
