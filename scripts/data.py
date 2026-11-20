"""Load, localise and validate the site data in data/."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NamedTuple

import yaml

LANGS = ("en", "it")
LIST_FILES = ("news", "talks", "projects", "teaching", "roles", "software")

REQUIRED = {
    "news": ("date", "text"),
    "talks": ("date", "title", "event", "place", "kind"),
    "projects": ("title", "role", "period", "kind"),
    "teaching": ("title", "programme", "level", "language", "years"),
    "roles": ("title", "org", "start", "kind"),
    "software": ("name", "repo"),
}
ENUMS = {
    ("talks", "kind"): {"talk", "poster", "invited", "keynote", "organizer", "committee", "chair"},
    ("projects", "kind"): {"funded", "open-resource", "research"},
    ("teaching", "level"): {"BSc", "MSc", "Master", "PhD", "open"},
    ("roles", "kind"): {"position", "visiting", "service", "honor", "education", "membership"},
}
# Content that must never be published (confidential / unpublished work).
FORBIDDEN = [
    re.compile(p, re.I)
    for p in (r"anonymous\.4open\.science", r"\bIS-Score\b", r"MERE-D-\d", r"\bLorenz\b",
              r"Partially Observed Multivariate Functional")
] + [re.compile(r"\bFCST\b"), re.compile(r"\bMERE\b")]  # case-sensitive code names


class Localized(NamedTuple):
    text: str
    lang: str


def tr(value: Any, lang: str) -> Localized:
    """Return text in `lang`, falling back to the other language (and saying which)."""
    if value is None:
        return Localized("", lang)
    if isinstance(value, dict):
        if value.get(lang):
            return Localized(str(value[lang]), lang)
        for other in LANGS:
            if value.get(other):
                return Localized(str(value[other]), other)
        return Localized("", lang)
    return Localized(str(value), lang)


@dataclass
class SiteData:
    profile: dict = field(default_factory=dict)
    news: list = field(default_factory=list)
    talks: list = field(default_factory=list)
    projects: list = field(default_factory=list)
    teaching: list = field(default_factory=list)
    roles: list = field(default_factory=list)
    software: list = field(default_factory=list)
    publications: list = field(default_factory=list)
    publications_meta: dict = field(default_factory=dict)
    software_meta: dict = field(default_factory=dict)


def _yaml(path: Path, default):
    if not path.exists():
        return default
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return default if loaded is None else loaded


def _json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_all(data_dir: Path) -> SiteData:
    d = SiteData(profile=_yaml(data_dir / "profile.yml", {}))
    for key, default in (("affiliation", {}), ("contact", {}), ("links", []), ("research_themes", [])):
        d.profile.setdefault(key, default)
    for name in LIST_FILES:
        setattr(d, name, _yaml(data_dir / f"{name}.yml", []))
    pubs = _json(data_dir / "publications.json", {"items": []})
    d.publications = pubs.get("items", [])
    d.publications_meta = {k: v for k, v in pubs.items() if k != "items"}
    d.software_meta = _json(data_dir / "software.json", {})
    return d


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def validate(d: SiteData) -> list[str]:
    errors: list[str] = []
    for name in LIST_FILES:
        items = getattr(d, name)
        if not isinstance(items, list):
            errors.append(f"{name}.yml: must be a list")
            continue
        seen = set()
        for i, item in enumerate(items):
            ident = item.get("id", item.get("name", f"#{i}"))
            if ident in seen:
                errors.append(f"{name}.yml: duplicate id '{ident}'")
            seen.add(ident)
            for key in REQUIRED[name]:
                if item.get(key) in (None, ""):
                    errors.append(f"{name}.yml: item '{ident}' missing '{key}'")
            for (fname, key), allowed in ENUMS.items():
                if fname == name and key in item and item[key] not in allowed:
                    errors.append(f"{name}.yml: item '{ident}' {key}='{item[key]}' not in {sorted(allowed)}")
    themes = {t["id"] for t in d.profile.get("research_themes", [])}
    for p in d.publications:
        for t in p.get("themes", []):
            if t not in themes:
                errors.append(f"publications: '{p.get('id')}' unknown theme '{t}'")
    def _check_maps(obj, where):
        if isinstance(obj, dict):
            keys = set(obj)
            if keys & set(LANGS) and not keys <= set(LANGS):
                errors.append(f"{where}: localized text split by an unquoted comma {sorted(map(str, keys))} - wrap the text in quotes")
            for v in obj.values():
                _check_maps(v, where)
        elif isinstance(obj, list):
            for v in obj:
                _check_maps(v, where)

    _check_maps(d.profile, "profile.yml")
    for name in LIST_FILES:
        _check_maps(getattr(d, name), f"{name}.yml")
    everything = [d.profile] + [getattr(d, n) for n in LIST_FILES] + [d.publications]
    for s in _strings(everything):
        for pat in FORBIDDEN:
            if pat.search(s):
                errors.append(f"forbidden content matched {pat.pattern!r}: {s[:60]!r}")
    return errors


def drafts(d: SiteData) -> list[str]:
    out = []
    if d.profile.get("draft"):
        out.append("profile.yml")
    for name in LIST_FILES:
        for item in getattr(d, name):
            if item.get("draft"):
                out.append(f"{name}.yml: {item.get('id', item.get('name'))}")
    return out
