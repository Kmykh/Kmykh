"""
Incrusta Titillium Web (licencia OFL, ver scripts/fonts/OFL.txt) dentro de los SVG.

GitHub muestra los SVG como <img>, así que no pueden cargar fuentes externas:
la fuente va en base64, recortada a los caracteres que usa cada archivo.
"""
import base64
import html
import re
from io import BytesIO
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

DIR = Path(__file__).resolve().parent / "fonts"
FILES = {700: "TitilliumWeb-Bold.ttf", 900: "TitilliumWeb-Black.ttf"}
FAMILY = "TW"
STACK = f"{FAMILY},'Titillium Web',Inter,'Segoe UI',-apple-system,Helvetica,Arial,sans-serif"


_metrics = {}


def text_width(text: str, size: float, weight=700) -> float:
    """Ancho real del texto en px con Titillium Web (para alinear sin adivinar)."""
    if weight not in _metrics:
        font = TTFont(DIR / FILES[weight])
        _metrics[weight] = (font.getBestCmap(), font["hmtx"].metrics, font["head"].unitsPerEm)
    cmap, hmtx, upm = _metrics[weight]
    return sum(hmtx[cmap[ord(ch)]][0] if ord(ch) in cmap else upm / 2 for ch in text) * size / upm


def font_css(svg_body: str, weights=(700, 900)) -> str:
    """@font-face con solo los glifos presentes en el texto del SVG."""
    text = html.unescape(re.sub(r"<style.*?</style>|<[^>]+>", " ", svg_body, flags=re.S))
    chars = "".join(sorted(set(text) | {" "}))
    css = []
    for w in weights:
        font = TTFont(DIR / FILES[w], recalcTimestamp=False)  # mismo SVG en cada build
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.drop_tables += ["FFTM"]
        sub = subset.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(font)
        buf = BytesIO()
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        css.append(f"@font-face{{font-family:{FAMILY};font-weight:{w};"
                   f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(css)
