#!/usr/bin/env python3
"""
Banner animado del perfil de Kmykh: terminal "vim profile.yml" con retrato
en puntos (dithering 1-bit Floyd-Steinberg) que se transforma en los logos
del stack y vuelve al retrato.

Uso (desde la raíz del repo):
    pip install -r scripts/banner/requirements.txt
    python3 scripts/banner/generate.py

Entradas:
    assets/source/portrait.png      foto con fondo transparente
    scripts/banner/logos/*.png      siluetas (negro sobre transparente)
Salida:
    assets/banner-dark.svg, assets/banner-light.svg
"""
from __future__ import annotations

from html import escape
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

ROOT = Path(__file__).resolve().parents[2]
PORTRAIT = ROOT / "assets/source/portrait.png"
LOGOS_DIR = Path(__file__).resolve().parent / "logos"
OUT = ROOT / "assets"

# ─────────────── configuración ───────────────
W, H = 1180, 610
GRID_W, GRID_H = 300, 340          # resolución del retrato en puntos
FRAME = (49, 124, 390, 414)        # x, y, w, h del área VISUAL.MAP
MAX_POINTS = 18_000
TRAVELLERS = 700                    # puntos que viajan entre formas
LOGO_POINTS = 2_200                 # densidad de cada logo cuando se queda quieto
LOGO_ORDER = ["react", "flutter", "springboot"]
PORTRAIT_HOLD, MORPH, LOGO_HOLD = 4.0, 1.3, 3.2
INTRO = 2.4
SEED = 2026
HANDLE = "@Kmykh"

YAML = [
    (0, "profile", ""),
    (1, "subject", "Maykol"),
    (1, "role", "Software Engineer · Web Developer"),
    (1, "origin", "Lima, Perú"),
    (1, "focus", "Webs animadas · Rendimiento · UX"),
    (1, "status", "Co-founder @ MindaCode"),
    (1, "craft", "Motion fluido sin sacrificar velocidad"),
    (0, "stack", ""),
    (1, "frontend", "React · TypeScript · HTML/CSS"),
    (1, "backend", "Spring Boot · ASP.NET Core"),
    (1, "mobile", "Flutter · Dart"),
    (1, "data", "PostgreSQL · Supabase"),
    (1, "iot", "ESP32 · MQTT"),
    (0, "contact", ""),
    (1, "linkedin", "/in/TU-USUARIO"),
    (1, "github", "Kmykh"),
    (1, "timezone", "UTC-5 · Lima"),
]

THEMES = {
    "dark": {
        "bg": "#0a0e0c", "panel": "#0e1411", "panel2": "#111a15", "line": "#21302a",
        "muted": "#7f8c85", "text": "#e9f2ec",
        "dots": "#22c55e", "accent": "#f97316", "shadow": "#020504",
    },
    "light": {
        "bg": "#f2f8f4", "panel": "#ffffff", "panel2": "#f3faf5", "line": "#cfe2d6",
        "muted": "#6b7d72", "text": "#112017",
        "dots": "#15803d", "accent": "#ea580c", "shadow": "#9fbfab",
    },
}
MONO = "ui-monospace,SFMono-Regular,'JetBrains Mono',Menlo,Consolas,monospace"


# ─────────────── imagen → puntos ───────────────
def dither(gray: np.ndarray) -> np.ndarray:
    """Floyd-Steinberg serpentino. Devuelve True donde el píxel queda encendido."""
    img = gray.astype(np.float32) / 255.0
    h, w = img.shape
    out = np.zeros((h, w), bool)
    for y in range(h):
        forward = y % 2 == 0
        step = 1 if forward else -1
        for x in (range(w) if forward else range(w - 1, -1, -1)):
            on = img[y, x] >= 0.5
            out[y, x] = on
            e = img[y, x] - (1.0 if on else 0.0)
            if 0 <= x + step < w:
                img[y, x + step] += e * 0.4375
            if y + 1 < h:
                if 0 <= x - step < w:
                    img[y + 1, x - step] += e * 0.1875
                img[y + 1, x] += e * 0.3125
                if 0 <= x + step < w:
                    img[y + 1, x + step] += e * 0.0625
    return out


def portrait_points(theme: str, rng) -> np.ndarray:
    src = Image.open(PORTRAIT).convert("RGBA").resize((GRID_W, GRID_H), Image.Resampling.LANCZOS)
    alpha = np.asarray(src.getchannel("A"), np.float32) / 255
    # desvanece los hombros hacia abajo
    fade_y = np.clip((GRID_H - np.arange(GRID_H)) / 80, 0, 1)[:, None]
    xs_ = np.arange(GRID_W)
    fade_x = np.clip(np.minimum(xs_, GRID_W - 1 - xs_) / 45, 0, 1)[None, :]
    alpha = alpha * fade_y * fade_x
    base = Image.new("RGBA", src.size, "black" if theme == "dark" else "white")
    base.alpha_composite(src)
    g = ImageOps.autocontrast(ImageOps.grayscale(src.convert("RGB")), cutoff=1)
    g = g.filter(ImageFilter.UnsharpMask(radius=2, percent=170, threshold=1))
    v = np.asarray(g, np.float32) / 255
    if theme == "dark":
        v = 0.07 + 0.93 * v ** 1.35          # sombras con algo de puntos, rasgos con contraste
    else:
        v = v ** 0.55                          # aclara la piel: solo los rasgos quedan marcados
    v = np.where(alpha > 0.05, v, 0.0 if theme == "dark" else 1.0)
    bits = dither(v * 255)
    lit = bits if theme == "dark" else ~bits
    lit &= rng.random(alpha.shape) < np.clip(alpha * 1.15, 0, 1)
    ys, xs = np.nonzero(lit)
    fx, fy, fw, fh = FRAME
    pts = np.column_stack((fx + (fw - GRID_W) / 2 + xs, fy + (fh - GRID_H) / 2 + ys)).astype(np.float32)
    if len(pts) > MAX_POINTS:
        pts = pts[rng.choice(len(pts), MAX_POINTS, replace=False)]
    return pts


def logo_points(name: str, n: int, rng) -> np.ndarray:
    img = Image.open(LOGOS_DIR / f"{name}.png").convert("RGBA")
    img.thumbnail((400, 400))
    a = np.asarray(img.getchannel("A"))
    ys, xs = np.nonzero(a > 127)
    fx, fy, fw, fh = FRAME
    s = 230 / 400
    cx, cy = fx + fw / 2, fy + fh / 2 - 6
    pts = np.column_stack((cx - 200 * s + xs * s, cy - 200 * s + ys * s)).astype(np.float32)
    return pts[rng.choice(len(pts), n, replace=len(pts) < n)]


# ─────────────── utilidades SVG ───────────────
def f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def runs(points: np.ndarray) -> str:
    """Une puntos horizontales contiguos en tramos de path (archivo más liviano)."""
    p = sorted({(int(x), int(y)) for x, y in np.rint(points)}, key=lambda q: (q[1], q[0]))
    d, i = [], 0
    while i < len(p):
        x0, y = p[i]; x1 = x0; i += 1
        while i < len(p) and p[i][1] == y and p[i][0] <= x1 + 1:
            x1 = p[i][0]; i += 1
        d.append(f"M{x0} {y}h{x1 - x0 + 1}")
    return "".join(d)


def assign(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    r, c = linear_sum_assignment(cdist(src, dst, "sqeuclidean"))
    out = np.empty_like(dst); out[r] = dst[c]
    return out


# ─────────────── render ───────────────
def render(theme: str, portrait: np.ndarray, logos: dict, rng) -> str:
    t = THEMES[theme]
    fx, fy, fw, fh = FRAME

    # línea de tiempo: retrato → logo1 → logo2 → logo3 → retrato
    start = portrait[rng.choice(len(portrait), TRAVELLERS, replace=False)]
    frames, times = [start, start], [0.0, PORTRAIT_HOLD]
    cur = start
    for name in LOGO_ORDER:
        cur = assign(cur, logos[name]["travel"])
        frames += [cur, cur]
        times += [times[-1] + MORPH, times[-1] + MORPH + LOGO_HOLD]
    frames.append(start); times.append(times[-1] + MORPH)
    total = times[-1]
    kt = ";".join(f"{v / total:.4f}" for v in times)
    nf = len(frames)
    anim = lambda attr, vals: (f'<animate attributeName="{attr}" begin="{INTRO}s" dur="{f(total)}s" '
                               f'repeatCount="indefinite" keyTimes="{kt}" values="{vals}"/>')

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
             f'aria-label="Maykol (Kmykh) — perfil animado: retrato en puntos y profile.yml">')
    s.append(f'<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="12" '
             f'stdDeviation="16" flood-color="{t["shadow"]}" flood-opacity=".28"/></filter>'
             f'<clipPath id="clip"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="3"/></clipPath>'
             f'<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["dots"]}" stop-opacity="0"/>'
             f'<stop offset="1" stop-color="{t["dots"]}" stop-opacity=".35"/></linearGradient></defs>')
    # ventana
    s.append(f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>'
             f'<rect x="13" y="13" width="1154" height="584" rx="13" fill="{t["panel"]}" stroke="{t["line"]}" filter="url(#sh)"/>'
             f'<path d="M13 62H1167" stroke="{t["line"]}"/>'
             '<circle cx="38" cy="38" r="6" fill="#FF5F57"/><circle cx="59" cy="38" r="6" fill="#FEBC2E"/>'
             '<circle cx="80" cy="38" r="6" fill="#28C840"/>'
             f'<text x="590" y="43" text-anchor="middle" fill="{t["muted"]}" font-family="{MONO}" font-size="13" letter-spacing=".4">vim profile.yml</text>')
    # panel izquierdo
    s.append(f'<rect x="35" y="88" width="418" height="472" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>'
             f'<path d="M35 124H453" stroke="{t["line"]}"/>'
             f'<text x="49" y="111" fill="{t["accent"]}" font-family="{MONO}" font-size="13" font-weight="700" letter-spacing="1.2">VISUAL.MAP</text>'
             f'<text x="438" y="111" text-anchor="end" fill="{t["muted"]}" font-family="{MONO}" font-size="11">{GRID_W}×{GRID_H} / 1-BIT</text>'
             f'<path d="M49 141h12M49 141v12M439 141h-12M439 141v12M49 539h12M49 539v-12M439 539h-12M439 539v-12" '
             f'fill="none" stroke="{t["accent"]}" opacity=".6"/>')
    s.append(f'<g clip-path="url(#clip)" shape-rendering="crispEdges">')

    # retrato: visible desde el inicio (también en vistas estáticas); se apaga mientras están los logos
    op = ["1", "1"] + ["0"] * (nf - 3) + ["1"]
    s.append(f'<path d="{runs(portrait)}" fill="none" stroke="{t["dots"]}" stroke-width="1">{anim("opacity", ";".join(op))}</path>')

    # viajeros
    tv = ["0", "0"] + ["1"] * (nf - 3) + ["0"]
    for i in range(TRAVELLERS):
        pos = ";".join(f"{f(fr[i, 0])} {f(fr[i, 1])}" for fr in frames)
        s.append(f'<path d="M-.7-.7h1.4v1.4h-1.4z" fill="{t["dots"]}" opacity="0">'
                 f'<animateTransform attributeName="transform" type="translate" begin="{INTRO}s" dur="{f(total)}s" '
                 f'repeatCount="indefinite" keyTimes="{kt}" values="{pos}"/>{anim("opacity", ";".join(tv))}</path>')

    # logos densos durante cada pausa
    for k, name in enumerate(LOGO_ORDER):
        v = ["0"] * nf; v[2 + 2 * k] = v[3 + 2 * k] = ".85"
        s.append(f'<path d="{runs(logos[name]["hold"])}" fill="none" stroke="{t["dots"]}" stroke-width="1" opacity="0">'
                 f'{anim("opacity", ";".join(v))}</path>')

    # barrido de escaneo al cargar
    s.append(f'<rect x="{fx}" y="{fy - 60}" width="{fw}" height="60" fill="url(#scan)" opacity="0">'
             f'<animate attributeName="y" begin="0s" dur="{INTRO}s" values="{fy - 60};{fy + fh}" fill="freeze"/>'
             f'<animate attributeName="opacity" begin="0s" dur="{INTRO}s" values="1;1;0" keyTimes="0;.9;1" fill="freeze"/></rect>')
    s.append("</g>")
    s.append(f'<text x="58" y="551" fill="{t["muted"]}" font-family="{MONO}" font-size="10">'
             f'PTS {len(portrait):05d} · FS/SERPENTINE · {" → ".join(n.upper() for n in LOGO_ORDER)}</text>')

    # panel derecho: profile.yml
    s.append(f'<rect x="474" y="88" width="672" height="472" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>'
             f'<path d="M474 124H1146" stroke="{t["line"]}"/>'
             f'<text x="490" y="111" font-family="{MONO}"><tspan fill="{t["text"]}" font-size="13" font-weight="700">profile.yml</tspan>'
             f'<tspan fill="{t["muted"]}" font-size="11" dx="8">[YAML]</tspan></text>'
             f'<rect x="1010" y="94" width="118" height="24" rx="12" fill="{t["accent"]}" fill-opacity=".14" stroke="{t["accent"]}"/>'
             f'<text x="1069" y="111" text-anchor="middle" fill="{t["accent"]}" font-family="{MONO}" font-size="13" font-weight="700">{HANDLE}</text>')
    y = 148.0
    for i, (ind, k, v) in enumerate(YAML, 1):
        s.append(f'<text x="506" y="{f(y)}" text-anchor="end" fill="{t["muted"]}" opacity=".5" font-family="{MONO}" font-size="13">{i}</text>')
        if ind == 0:
            body = f'<tspan fill="{t["accent"]}" font-weight="700">{escape(k)}:</tspan>'
            x = 525
        else:
            body = f'<tspan fill="{t["dots"]}">{escape(k)}: </tspan><tspan fill="{t["text"]}">{escape(v)}</tspan>'
            x = 542
        s.append(f'<g opacity="0"><animate attributeName="opacity" begin="{.15 + i * .07:.2f}s" dur=".35s" values="0;1" fill="freeze"/>'
                 f'<text x="{x}" y="{f(y)}" font-family="{MONO}" font-size="13">{body}</text></g>')
        y += 21.5
    # cursor
    s.append(f'<rect x="525" y="{f(y - 14)}" width="8" height="17" fill="{t["dots"]}">'
             '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')
    # barra de estado de vim
    nbytes = sum(len(k) + len(v) + 4 for _, k, v in YAML)
    s.append(f'<path d="M474 526H1146" stroke="{t["line"]}"/>'
             f'<rect x="475" y="527" width="670" height="32" fill="{t["panel"]}"/>'
             f'<rect x="485" y="533" width="72" height="20" rx="3" fill="{t["dots"]}"/>'
             f'<text x="521" y="547" text-anchor="middle" fill="{t["bg"]}" font-family="{MONO}" font-size="11" font-weight="700">NORMAL</text>'
             f'<text x="569" y="547" fill="{t["text"]}" font-family="{MONO}" font-size="12" font-weight="600">profile.yml</text>'
             f'<text x="740" y="547" fill="{t["muted"]}" font-family="{MONO}" font-size="11">[utf-8]</text>'
             f'<circle cx="822" cy="543" r="4" fill="{t["accent"]}"><animate attributeName="opacity" values="1;.3;1" dur="2s" repeatCount="indefinite"/></circle>'
             f'<text x="832" y="547" fill="{t["muted"]}" font-family="{MONO}" font-size="11">disponible</text>'
             f'<text x="1134" y="547" text-anchor="end" fill="{t["muted"]}" font-family="{MONO}" font-size="11">'
             f'{len(YAML)}L, {nbytes}B  100%  {len(YAML) + 1}:1</text>')
    s.append("</svg>")
    return "".join(s)


def main():
    if not PORTRAIT.exists():
        raise SystemExit(f"Falta la foto: {PORTRAIT}")
    for i, theme in enumerate(THEMES):
        rng = np.random.default_rng(SEED + i)
        portrait = portrait_points(theme, rng)
        logos = {n: {"travel": logo_points(n, TRAVELLERS, rng), "hold": logo_points(n, LOGO_POINTS, rng)} for n in LOGO_ORDER}
        out = OUT / f"banner-{theme}.svg"
        out.write_text(render(theme, portrait, logos, rng), encoding="utf-8")
        print(f"{out.relative_to(ROOT)}: {out.stat().st_size / 1024:.0f} KB · {len(portrait)} puntos")


if __name__ == "__main__":
    main()
