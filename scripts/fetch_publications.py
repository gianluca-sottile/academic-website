"""Refresh data/publications.json from OpenAlex (works linked to the ORCID iD).

Safe by design: if the API cannot be reached the previous file is kept untouched.
Manual corrections live in data/publications.overrides.yml.
Optional: set OPENALEX_MAILTO (repository secret/variable) to use OpenAlex's polite pool.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
ORCID = "0000-0001-9347-7251"
OPENALEX_URL = "https://api.openalex.org/works"
UA = "academic-website publication refresher (+https://github.com/gianluca-sottile/academic-website)"

TYPE_MAP = {"article": "article", "review": "article", "letter": "article",
            "book-chapter": "chapter", "conference-paper": "proceedings",
            "proceedings-article": "proceedings", "book": "book"}
EXCLUDED_DOI_PREFIXES = ("10.6084/", "10.5281/", "10.32614/", "10.48550/", "10.1101/", "10.2139/", "10.5194/egusphere")
SHRINK_LIMIT = 0.8  # refuse to overwrite if the list loses more than 20% of its items
TYPE_RANK = {"article": 0, "proceedings": 1, "chapter": 2, "book": 3}


def norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


SUBSCRIPT = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def clean_title(raw: str) -> str:
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = re.sub(r"\$\$_\{?(\d+)\}?\$\$", lambda m: m.group(1).translate(SUBSCRIPT), text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _safe(url):
    return url if isinstance(url, str) and url.startswith(("http://", "https://")) else None


def _doi(raw: str | None) -> str | None:
    if not raw:
        return None
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", raw).lower()


def _venue(loc: dict, source: dict) -> str:
    kind = source.get("type")
    if kind == "repository":
        return ""
    if kind == "ebook platform":
        return loc.get("raw_source_name") or ""
    return source.get("display_name") or loc.get("raw_source_name") or ""


def normalize(work: dict) -> dict | None:
    pub_type = TYPE_MAP.get(work.get("type") or "")
    doi = _doi(work.get("doi"))
    if pub_type is None or (doi and doi.startswith(EXCLUDED_DOI_PREFIXES)):
        return None
    title = clean_title(work.get("title") or "")
    if not title or title.lower().startswith("moesm"):
        return None
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    oa = work.get("open_access") or {}
    ident = doi or "oa-" + norm_title(title).replace(" ", "-")[:60]
    return {
        "id": ident,
        "doi": doi,
        "title": title,
        "authors": [a["author"].get("display_name") for a in work.get("authorships") or []
                    if a.get("author") and a["author"].get("display_name")],
        "venue": _venue(loc, source),
        "year": work.get("publication_year"),
        "type": pub_type,
        "url": f"https://doi.org/{doi}" if doi else (_safe(loc.get("landing_page_url")) or ""),
        "oa_url": _safe(oa.get("oa_url")),
        "citations": work.get("cited_by_count"),
        "topic": (work.get("primary_topic") or {}).get("display_name", ""),
        "themes": [],
        "selected": False,
        "links": [],
    }


def _better(a: dict, b: dict) -> dict:
    """Pick the record to keep among duplicates: DOI first, then type, then citations."""
    key = lambda p: (p["doi"] is None, TYPE_RANK.get(p["type"], 9), -(p["citations"] or 0))
    return a if key(a) <= key(b) else b


def dedupe(items: list[dict]) -> list[dict]:
    """Merge by DOI first; merge by title only when one of the two records has no DOI."""
    by_doi: dict[str, dict] = {}
    no_doi: list[dict] = []
    for p in items:
        if p["doi"]:
            by_doi[p["doi"]] = _better(by_doi[p["doi"]], p) if p["doi"] in by_doi else p
        else:
            no_doi.append(p)
    titles = {norm_title(p["title"]) for p in by_doi.values()}
    kept: dict[str, dict] = {}
    for p in no_doi:
        k = norm_title(p["title"])
        if k in titles:
            continue
        kept[k] = _better(kept[k], p) if k in kept else p
    return list(by_doi.values()) + list(kept.values())


def suggest_themes(p: dict, themes_cfg: list[dict]) -> list[str]:
    hay = f"{p['title']} {p.get('topic', '')}".lower()
    return [t["id"] for t in themes_cfg if any(k.lower() in hay for k in t.get("openalex_keywords", []))]


def process(works: list[dict], overrides: dict, themes_cfg: list[dict]) -> list[dict]:
    excl = [re.compile(x, re.I) for x in overrides.get("exclude_titles") or []]
    items = dedupe([p for p in (normalize(w) for w in works) if p and not any(r.search(p["title"]) for r in excl)])
    hide = {str(x).lower() for x in overrides.get("hide") or []}
    selected = {str(x).lower() for x in overrides.get("selected") or []}
    themes = {str(k).lower(): v for k, v in (overrides.get("themes") or {}).items()}
    links = {str(k).lower(): v for k, v in (overrides.get("links") or {}).items()}
    out = []
    for p in items:
        if p["id"] in hide:
            continue
        p["themes"] = themes.get(p["id"], suggest_themes(p, themes_cfg))
        p["selected"] = p["id"] in selected
        p["links"] = links.get(p["id"], [])
        out.append(p)
    for extra in overrides.get("extra") or []:
        rec = {"doi": None, "authors": [], "venue": "", "url": "", "oa_url": None, "citations": None,
               "topic": "", "themes": [], "links": [], **extra}
        rec["selected"] = str(rec["id"]).lower() in selected
        out.append(rec)
    out.sort(key=lambda p: (-(p.get("year") or 0), p["title"].lower()))
    return out


def fetch_openalex(orcid: str, session: requests.Session, retries: int = 3) -> list[dict]:
    works, cursor = [], "*"
    mailto = os.environ.get("OPENALEX_MAILTO")
    while cursor:
        params = {"filter": f"author.orcid:{orcid}", "per_page": 200, "cursor": cursor}
        if mailto:
            params["mailto"] = mailto
        for attempt in range(retries):
            try:
                r = session.get(OPENALEX_URL, params=params, timeout=20)
                r.raise_for_status()
                break
            except requests.RequestException:
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)
        page = r.json()
        works.extend(page.get("results", []))
        cursor = (page.get("meta") or {}).get("next_cursor")
    return works


def write_if_changed(path: Path, items: list[dict]) -> bool:
    payload = {"updated": dt.date.today().isoformat(), "source": f"OpenAlex (ORCID {ORCID})", "items": items}
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if old.get("items") == items:
            return False
        if len(items) < SHRINK_LIMIT * len(old.get("items", [])):
            print(f"WARNING: list would shrink from {len(old['items'])} to {len(items)} items; keeping the previous file", file=sys.stderr)
            return False
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "publications.json"))
    ap.add_argument("--overrides", default=str(ROOT / "data" / "publications.overrides.yml"))
    ap.add_argument("--profile", default=str(ROOT / "data" / "profile.yml"))
    ap.add_argument("--from-file", help="use a saved OpenAlex response instead of the API")
    ap.add_argument("--retries", type=int, default=3)
    args = ap.parse_args(argv)

    ov_path = Path(args.overrides)
    overrides = (yaml.safe_load(ov_path.read_text()) or {}) if ov_path.exists() else {}
    profile = yaml.safe_load(Path(args.profile).read_text()) or {}
    themes_cfg = profile.get("research_themes", [])

    if args.from_file:
        works = json.loads(Path(args.from_file).read_text())["results"]
    else:
        session = requests.Session()
        session.headers["User-Agent"] = UA
        try:
            works = fetch_openalex(ORCID, session, args.retries)
        except (requests.RequestException, ValueError) as exc:
            print(f"WARNING: OpenAlex unreachable ({exc}); keeping previous publications.json", file=sys.stderr)
            return 0
    if not works:
        print("WARNING: no works returned; keeping previous publications.json", file=sys.stderr)
        return 0
    items = process(works, overrides, themes_cfg)
    changed = write_if_changed(Path(args.out), items)
    print(f"{len(items)} publications ({'updated' if changed else 'unchanged'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
