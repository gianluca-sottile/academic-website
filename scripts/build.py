"""Build the static site: data/*.yml + templates -> site/ (EN at /, IT at /it/)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


import os

import yaml

import data  # noqa: E402
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
LANGS = ("en", "it")
DEFAULT_LANG = "en"
BASE_URL = "https://gianlucasottile.rbind.io"
PAGES = ("index", "publications", "teaching", "projects", "software", "talks", "cv")


SAFE_SCHEMES = ("http://", "https://", "mailto:", "/")


def safe_url(url) -> str:
    url = (url or "").strip()
    return url if url.startswith(SAFE_SCHEMES) and not url.startswith("//") else ""


def url_for(page: str, lang: str) -> str:
    prefix = "/" if lang == DEFAULT_LANG else f"/{lang}/"
    return prefix if page == "index" else f"{prefix}{page}/"


def _env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(ROOT / "src" / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["url_for"] = url_for
    env.globals["LANGS"] = LANGS
    env.globals["BASE_URL"] = BASE_URL
    env.filters["safe_url"] = safe_url
    return env


def _out_path(out_dir: Path, page: str, lang: str) -> Path:
    rel = url_for(page, lang).strip("/")
    return out_dir / rel / "index.html" if rel else out_dir / "index.html"


def render_pages(env: Environment, context: dict, out_dir: Path, pages=PAGES) -> list[Path]:
    written = []
    for lang in LANGS:
        for page in pages:
            tpl = env.get_template(f"{page}.html")
            t = context.get("strings", {}).get(lang, {})
            html = tpl.render(lang=lang, page=page, t=t, **context)
            path = _out_path(out_dir, page, lang)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
            written.append(path)
    return written


def copy_static(out_dir: Path) -> None:
    for src in (ROOT / "static", ROOT / "src" / "assets"):
        if src.exists():
            shutil.copytree(src, out_dir if src.name == "static" else out_dir / "assets", dirs_exist_ok=True)


def build(data_dir: Path, out_dir: Path) -> list[Path]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    context = load_context(data_dir)
    written = render_pages(_env(), context, out_dir)
    copy_static(out_dir)
    return written


class ValidationError(Exception):
    pass


HERO_SECTIONS = ("publications", "software", "teaching", "projects", "career", "talks", "contact")


def hero_paths(n: int = len(HERO_SECTIONS), width: float = 640, height: float = 420) -> list[dict]:
    """Deterministic lasso-like coefficient paths: zero until a knot, then piecewise linear to a spread end value."""
    zero = height / 2
    knots = [0.10, 0.18, 0.27, 0.36, 0.47, 0.58, 0.70][:n]
    offsets = (-185, -128, -72, -26, 58, 118, 178)[:n]
    ends = [zero + o for o in offsets]
    bends = [0.55, -0.25, 0.8, 1.6, -0.6, 0.15, 0.45]
    paths = []
    for i, (k, end) in enumerate(zip(knots, ends)):
        x0 = k * width
        xm = x0 + (width - x0) * 0.45
        ym = zero + (end - zero) * (0.5 + bends[i] * 0.4)
        d = f"M0 {zero:.1f} L{x0:.1f} {zero:.1f} L{xm:.1f} {ym:.1f} L{width:.1f} {end:.1f}"
        paths.append({"d": d, "x0": x0, "end_y": end, "section": HERO_SECTIONS[i]})
    return paths


def _strings(lang: str) -> dict:
    return yaml.safe_load((ROOT / "src" / "i18n" / f"{lang}.yml").read_text(encoding="utf-8"))


def _production() -> bool:
    return os.environ.get("BUILD_ENV") == "production"


def load_context(data_dir: Path) -> dict:
    site = data.load_all(data_dir)
    errors = data.validate(site)
    if errors:
        raise ValidationError("\n".join(errors))
    pending = data.drafts(site)
    if pending:
        print(f"WARNING: {len(pending)} draft item(s) awaiting approval:", file=sys.stderr)
        for item in pending:
            print(f"  - {item}", file=sys.stderr)
    if _production() and site.profile.get("draft"):
        raise ValidationError("profile.yml is still a draft: approve it (remove 'draft: true') before a production build")
    if _production():
        for name in data.LIST_FILES:
            setattr(site, name, [i for i in getattr(site, name) if not i.get("draft")])
    meta = {k: v for k, v in site.software_meta.items()}
    counts = {
        "pubs": len(site.publications),
        "cites": sum(p.get("citations") or 0 for p in site.publications),
        "pkgs": sum(1 for s in site.software if s.get("cran")),
        "courses": sum(1 for c in site.teaching if c.get("current") and c.get("level") != "open"),
    }
    present = {
        "publications": bool(site.publications), "software": bool(site.software), "teaching": bool(site.teaching),
        "projects": bool(site.projects), "career": bool(site.roles), "talks": bool(site.talks), "contact": True,
        "news": bool(site.news),
    }
    hero = [p for p in hero_paths() if present.get(p["section"])]
    return {"site": site, "tr": data.tr, "drafts": pending, "hero": hero, "counts": counts, "present": present,
            "software_meta": meta, "strings": {l: _strings(l) for l in LANGS}}


def main(argv: list[str]) -> int:
    out = ROOT / "site"
    try:
        files = build(ROOT / "data", out)
    except ValidationError as exc:
        print(f"Data validation failed:\n{exc}", file=sys.stderr)
        return 1
    print(f"Built {len(files)} pages into {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
