"""Write _design/contenuti-da-rivedere.md: every draft item with EN and IT side by side."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import data  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def cell(v):
    if isinstance(v, dict) and set(v) <= {"en", "it"}:
        return v.get("en", "—"), v.get("it", "—")
    return str(v), str(v)


def main():
    d = data.load_all(ROOT / "data")
    out = ["# Contenuti da rivedere", "",
           "Ogni voce qui sotto è marcata `draft: true` nei file in `data/`. Quando va bene, togli la riga `draft: true` (o dimmelo e lo faccio io).", ""]
    groups = [("profile.yml", [d.profile] if d.profile.get("draft") else [])]
    groups += [(f"{n}.yml", [i for i in getattr(d, n) if i.get("draft")]) for n in data.LIST_FILES]
    for fname, items in groups:
        if not items:
            continue
        out += [f"## {fname}", ""]
        for it in items:
            out += [f"### {it.get('id', it.get('name', fname))}", "", "| campo | EN | IT |", "|---|---|---|"]
            for k, v in it.items():
                if k in ("id", "draft") or isinstance(v, list):
                    continue
                en, itv = cell(v)
                out.append(f"| {k} | {en.replace('|', '/').strip()} | {itv.replace('|', '/').strip()} |")
            out.append("")
    (ROOT / "_design" / "contenuti-da-rivedere.md").write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
