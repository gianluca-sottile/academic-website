"""Refresh data/software.json with CRAN and GitHub metadata. Failed lookups keep previous values."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
CRANDB = "https://crandb.r-pkg.org/{pkg}"
CRANLOGS = "https://cranlogs.r-pkg.org/downloads/total/last-month/{pkg}"
GITHUB = "https://api.github.com/repos/{repo}"
EMPTY = {"cran_version": None, "cran_published": None, "downloads_last_month": None, "gh_stars": None, "gh_url": None}


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "academic-website software refresher"
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    return s


def _get(s: requests.Session, url: str):
    try:
        r = s.get(url, timeout=20)
        r.raise_for_status()
        return r.json()
    except (requests.RequestException, ValueError):
        return None


def collect(packages: list[dict], old: dict, s: requests.Session) -> dict:
    meta = {}
    for p in packages:
        cur = {**EMPTY, **old.get(p["id"], {})}
        if p.get("cran"):
            info = _get(s, CRANDB.format(pkg=p["cran"]))
            if info:
                cur["cran_version"] = info.get("Version")
                cur["cran_published"] = (info.get("Date/Publication") or "")[:10] or None
            logs = _get(s, CRANLOGS.format(pkg=p["cran"]))
            if logs and isinstance(logs, list):
                cur["downloads_last_month"] = logs[0].get("downloads")
        gh = _get(s, GITHUB.format(repo=p["repo"]))
        if gh:
            cur["gh_stars"] = gh.get("stargazers_count")
            cur["gh_url"] = gh.get("html_url")
        meta[p["id"]] = cur
    return meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packages", default=str(ROOT / "data" / "software.yml"))
    ap.add_argument("--out", default=str(ROOT / "data" / "software.json"))
    args = ap.parse_args(argv)
    packages = yaml.safe_load(Path(args.packages).read_text()) or []
    out = Path(args.out)
    old = json.loads(out.read_text()) if out.exists() else {}
    meta = collect(packages, old, session())
    if meta != old:
        out.write_text(json.dumps(meta, indent=1) + "\n")
    print(f"{len(meta)} packages ({'updated' if meta != old else 'unchanged'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
