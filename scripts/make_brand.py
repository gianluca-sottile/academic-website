"""Generate brand SVGs (wordmark + quantile symbol) by outlining Latin Modern glyphs.

Latin Modern = the LaTeX typeface: a deliberate nod to the statistician's daily tool.
Run once; outputs are committed. Requires fontTools and the lm OTF fonts (texlive).
"""
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "assets" / "brand"
LM = Path("/usr/share/texmf/fonts/opentype/public/lm")
INK, PAPER, ACCENT, ACCENT_DARK = "#1F2A44", "#F7F4EE", "#D85A30", "#F0997B"


def text_path(font_file: str, text: str, size: float, x: float, y: float, tracking: float = 0.0) -> tuple[str, float]:
    font = TTFont(LM / font_file)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    pen = SVGPathPen(gs)
    cursor = x
    for ch in text:
        g = cmap[ord(ch)]
        tp = TransformPen(pen, (scale, 0, 0, -scale, cursor, y))
        gs[g].draw(tp)
        cursor += gs[g].width * scale + tracking
    return pen.getCommands(), cursor - tracking


def wordmark(ink: str, accent: str) -> str:
    top, w1 = text_path("lmroman10-regular.otf", "gianluca", 15, 2, 17, tracking=3.2)
    main, w2 = text_path("lmroman10-italic.otf", "sottile", 46, 0, 58)
    width = max(w1, w2) + 14
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} 74" role="img" aria-label="Gianluca Sottile">'
            f'<path fill="{ink}" d="{top}"/><path fill="{ink}" d="{main}"/>'
            f'<line x1="1" y1="67" x2="{width - 8:.1f}" y2="67" stroke="{accent}" stroke-width="0.8"/>'
            f'<circle cx="{width - 6:.1f}" cy="67" r="2.6" fill="{accent}"/></svg>')


def _bezier(t, p0, p1, p2, p3):
    u = 1 - t
    return tuple(u**3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t**3 * d for a, b, c, d in zip(p0, p1, p2, p3))


def symbol(bg: str, fg: str, accent: str, rounded: bool = True, dots: int = 5) -> str:
    g, _ = text_path("lmroman10-regular.otf", "G", 66, 7, 80)
    curve = ((62, 90), (96, 90), (68, 22), (102, 22))
    ts = (0.1, 0.3, 0.5, 0.7, 0.9) if dots == 5 else (0.2, 0.5, 0.8)
    jitter = (5, -5, 4, -5, 5) if dots == 5 else (5, -5, 5)
    circles = ""
    for t, j in zip(ts, jitter):
        x, y = _bezier(t, *curve)
        circles += f'<circle cx="{x + j:.1f}" cy="{y:.1f}" r="3.6" fill="{fg}"/>'
    c = curve
    rx = 22 if rounded else 0
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 112 112" role="img" aria-label="GS">'
            f'<rect width="112" height="112" rx="{rx}" fill="{bg}"/>'
            f'<path fill="{fg}" d="{g}"/>'
            f'<path d="M{c[0][0]} {c[0][1]} C {c[1][0]} {c[1][1]}, {c[2][0]} {c[2][1]}, {c[3][0]} {c[3][1]}" fill="none" stroke="{accent}" stroke-width="7" stroke-linecap="round"/>'
            f'{circles}</svg>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "wordmark.svg").write_text(wordmark(INK, ACCENT))
    (OUT / "wordmark-dark.svg").write_text(wordmark(PAPER, ACCENT_DARK))
    (OUT / "wordmark-inline.svg").write_text(wordmark("currentColor", "var(--accent)"))
    (OUT / "symbol.svg").write_text(symbol(INK, PAPER, ACCENT_DARK))
    (OUT / "favicon.svg").write_text(symbol(INK, PAPER, ACCENT_DARK, dots=3))


if __name__ == "__main__":
    main()
