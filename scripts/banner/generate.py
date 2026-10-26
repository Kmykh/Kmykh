#!/usr/bin/env python3
"""
Banner animado del perfil de Kmykh (temática F1): terminal "vim driver.yml"
con semáforo de salida y retrato en puntos (dithering 1-bit Floyd-Steinberg)
que se transforma en Flutter, IA, React y un monoplaza, y vuelve al retrato.

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

import sys
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fonts import STACK as DISP, font_css  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PORTRAIT = ROOT / "assets/source/portrait.png"
LOGOS_DIR = Path(__file__).resolve().parent / "logos"
OUT = ROOT / "assets"

# ─────────────── configuración ───────────────
W, H = 1180, 628
GRID_W, GRID_H = 300, 340          # resolución del retrato en puntos
FRAME = (49, 124, 390, 414)        # x, y, w, h del área ONBOARD
MAX_POINTS = 18_000
TRAVELLERS = 700                    # puntos que viajan entre formas
LOGO_DENSITY = .18                  # fracción de la silueta que se enciende cuando el logo se queda quieto
LOGO_ORDER = ["flutter", "ai", "react", "car"]
LOGO_LABEL = {"flutter": "FLUTTER", "ai": "IA", "react": "REACT", "car": "MONOPLAZA", "springboot": "SPRING"}
LOGO_SIZE = {"car": 340, "ai": 250}  # lado en px dentro del marco (por defecto 230)
PORTRAIT_HOLD, MORPH, LOGO_HOLD = 4.0, 1.3, 2.8
LIGHTS_ON, LIGHTS_GAP, LIGHTS_OUT = .2, .3, 2.0   # semáforo: se encienden de a uno y se apagan juntos
INTRO = 3.2                                      # el retrato empieza a transformarse después del escaneo
SEED = 2026
HANDLE = "@Kmykh"

YAML = [
    (0, "driver", ""),
    (1, "name", "Maykol Rojas"),
    (1, "role", "Software Engineer · Mobile & IA"),
    (1, "now", "IA en aplicaciones móviles"),
    (1, "focus", "Proyectos con IA · Apps móviles · Aplicaciones"),
    (1, "lead", "Aura Nova · Aliada (+ LumAI) · Vitalify"),
    (1, "craft", "UX Design · arquitecturas de software"),
    (1, "method", "Scrum · gestión de equipos"),
    (1, "ai", "Uso responsable · ética · sesgos · IA generativa"),
    (1, "team", "Co-founder @ MindaCode"),
    (0, "setup", ""),
    (1, "mobile", "Flutter · Dart"),
    (1, "backend", "Spring Boot · ASP.NET Core"),
    (1, "web", "React · Next.js · TypeScript"),
    (0, "pit_radio", ""),
    (1, "linkedin", "/in/maykol-jhordan-rojas-velasquez-7594a52a2"),
    (1, "email", "maycoljhordan07@gmail.com"),
    (1, "base", "Lima, Perú · UTC-5"),
]

THEMES = {
    "dark": {
        "bg": "#09090c", "carbon": "#101015", "panel": "#0f0f13", "panel2": "#131318", "line": "#26262f",
        "muted": "#8d8d9a", "key": "#a9a9b6", "text": "#f3f3f6", "portrait": "#ecedf2",
        "dots": "#ff2a1f", "accent": "#ff2a1f", "lamp": "#2b1716", "purple": "#b26bff",
        "green": "#2fdc6a", "kerb": "#f3f3f6", "shadow": "#000000",
    },
    "light": {
        "bg": "#f1f1f4", "carbon": "#e8e8ed", "panel": "#ffffff", "panel2": "#f8f8fa", "line": "#dcdce4",
        "muted": "#6a6a78", "key": "#4a4a57", "text": "#111116", "portrait": "#15151b",
        "dots": "#d81e10", "accent": "#d81e10", "lamp": "#ecdcda", "purple": "#7c3aed",
        "green": "#15803d", "kerb": "#ffffff", "shadow": "#8d8d9a",
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


def logo_points(name: str, n: int | None, rng) -> np.ndarray:
    """n puntos sobre la silueta; con n=None, según LOGO_DENSITY y el área en pantalla."""
    img = Image.open(LOGOS_DIR / f"{name}.png").convert("RGBA")
    img.thumbnail((400, 400))
    a = np.asarray(img.getchannel("A"))
    ys, xs = np.nonzero(a > 127)
    fx, fy, fw, fh = FRAME
    s = LOGO_SIZE.get(name, 230) / 400
    n = n or int(len(xs) * s * s * LOGO_DENSITY)
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

    # línea de tiempo: retrato → logo1 → … → logoN → retrato
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
    s.append(f'<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="12" '
             f'stdDeviation="16" flood-color="{t["shadow"]}" flood-opacity=".3"/></filter>'
             f'<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feDropShadow dx="0" dy="0" '
             f'stdDeviation="2.5" flood-color="{t["accent"]}" flood-opacity=".9"/></filter>'
             f'<clipPath id="clip"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="3"/></clipPath>'
             f'<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["dots"]}" stop-opacity="0"/>'
             f'<stop offset="1" stop-color="{t["dots"]}" stop-opacity=".35"/></linearGradient>'
             # fibra de carbono: tejido sarga 2x2
             f'<pattern id="carbon" width="8" height="8" patternUnits="userSpaceOnUse">'
             f'<rect width="8" height="8" fill="{t["bg"]}"/><rect width="4" height="2" fill="{t["carbon"]}"/>'
             f'<rect x="4" y="4" width="4" height="2" fill="{t["carbon"]}"/><rect x="6" width="2" height="4" fill="{t["carbon"]}"/>'
             f'<rect x="2" y="4" width="2" height="4" fill="{t["carbon"]}"/></pattern>'
             # piano (kerb) rojo y blanco que avanza
             f'<pattern id="kerb" width="36" height="10" patternUnits="userSpaceOnUse">'
             f'<rect width="36" height="10" fill="{t["kerb"]}"/><path d="M0 10L6 0H24L18 10Z" fill="{t["accent"]}"/>'
             f'<animateTransform attributeName="patternTransform" type="translate" from="0 0" to="-36 0" dur="1.8s" repeatCount="indefinite"/>'
             f'</pattern>'
             f'<clipPath id="kclip"><rect x="13" y="608" width="1154" height="9" rx="4.5"/></clipPath></defs>')
    # ventana
    s.append(f'<rect width="{W}" height="{H}" rx="18" fill="url(#carbon)"/>'
             f'<rect x="13" y="13" width="1154" height="584" rx="13" fill="{t["panel"]}" stroke="{t["line"]}" filter="url(#sh)"/>'
             f'<path d="M13 62H1167" stroke="{t["line"]}"/>'
             f'<rect x="13" y="608" width="1154" height="9" fill="url(#kerb)" clip-path="url(#kclip)"/>')
    # semáforo de salida (reemplaza los botones de la ventana): lights out and away we go
    s.append(f'<rect x="26" y="27" width="104" height="22" rx="11" fill="{t["panel2"]}" stroke="{t["line"]}"/>')
    for i in range(5):
        cx, d = 38 + i * 20, LIGHTS_ON + i * LIGHTS_GAP
        s.append(f'<circle cx="{cx}" cy="38" r="6" fill="{t["lamp"]}"/>'
                 f'<circle cx="{cx}" cy="38" r="6" fill="{t["accent"]}" filter="url(#glow)" opacity="0">'
                 f'<set attributeName="opacity" to="1" begin="{d:.2f}s" dur="{LIGHTS_OUT - d:.2f}s"/></circle>')
    s.append(f'<text x="590" y="43" text-anchor="middle" fill="{t["muted"]}" font-family="{MONO}" font-size="13" letter-spacing=".4">vim driver.yml</text>'
             f'<text x="1146" y="43" text-anchor="end" fill="{t["muted"]}" font-family="{MONO}" font-size="11" letter-spacing="1">GP LIMA · 2026</text>')
    # panel izquierdo: cámara onboard
    s.append(f'<rect x="35" y="88" width="418" height="472" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>'
             f'<path d="M35 124H453" stroke="{t["line"]}"/>'
             f'<text x="49" y="112" fill="{t["accent"]}" font-family="{DISP}" font-size="16" font-weight="900" font-style="italic" letter-spacing="1.5">ONBOARD</text>'
             f'<circle cx="143" cy="106" r="4" fill="{t["accent"]}"><animate attributeName="opacity" values="1;1;.15;.15" keyTimes="0;.5;.5;1" dur="1.4s" repeatCount="indefinite"/></circle>'
             f'<text x="152" y="110" fill="{t["muted"]}" font-family="{MONO}" font-size="10.5" letter-spacing="1">REC</text>'
             f'<text x="438" y="111" text-anchor="end" fill="{t["muted"]}" font-family="{MONO}" font-size="11">{GRID_W}×{GRID_H} / 1-BIT</text>'
             f'<path d="M49 141h12M49 141v12M439 141h-12M439 141v12M49 539h12M49 539v-12M439 539h-12M439 539v-12" '
             f'fill="none" stroke="{t["accent"]}" opacity=".6"/>')
    s.append(f'<g clip-path="url(#clip)" shape-rendering="crispEdges">')

    # retrato: visible desde el inicio (también en vistas estáticas); se apaga mientras están los logos
    op = ["1", "1"] + ["0"] * (nf - 3) + ["1"]
    s.append(f'<path d="{runs(portrait)}" fill="none" stroke="{t["portrait"]}" stroke-width="1">{anim("opacity", ";".join(op))}</path>')

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

    # barrido de escaneo al apagarse el semáforo
    scan = INTRO - LIGHTS_OUT
    s.append(f'<rect x="{fx}" y="{fy - 60}" width="{fw}" height="60" fill="url(#scan)" opacity="0">'
             f'<animate attributeName="y" begin="{LIGHTS_OUT}s" dur="{f(scan)}s" values="{fy - 60};{fy + fh}" fill="freeze"/>'
             f'<animate attributeName="opacity" begin="{LIGHTS_OUT}s" dur="{f(scan)}s" values="1;1;0" keyTimes="0;.9;1" fill="freeze"/></rect>')
    s.append("</g>")
    s.append(f'<text x="58" y="551" fill="{t["muted"]}" font-family="{MONO}" font-size="10">'
             f'PTS {len(portrait):05d} · FS/SERPENTINE · {" → ".join(LOGO_LABEL[n] for n in LOGO_ORDER)}</text>')

    # panel derecho: driver.yml
    s.append(f'<rect x="474" y="88" width="672" height="472" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>'
             f'<path d="M474 124H1146" stroke="{t["line"]}"/>'
             f'<text x="490" y="111" font-family="{MONO}"><tspan fill="{t["text"]}" font-size="13" font-weight="700">driver.yml</tspan>'
             f'<tspan fill="{t["muted"]}" font-size="11" dx="8">[YAML]</tspan></text>'
             f'<rect x="1010" y="94" width="118" height="24" rx="4" fill="{t["accent"]}" fill-opacity=".12" stroke="{t["accent"]}"/>'
             f'<text x="1069" y="111" text-anchor="middle" fill="{t["accent"]}" font-family="{DISP}" font-size="14" font-weight="900" letter-spacing=".5">{HANDLE}</text>')
    # tiempos por sector: se van llenando mientras carga el archivo
    seg_w = (670 - 2 * 3) / 3
    for k, col in enumerate([t["purple"], t["purple"], t["green"]]):
        x0 = 475 + k * (seg_w + 3)
        s.append(f'<rect x="{f(x0)}" y="124" width="{f(seg_w)}" height="3" fill="{t["line"]}"/>'
                 f'<rect x="{f(x0)}" y="124" width="0" height="3" fill="{col}">'
                 f'<animate attributeName="width" begin="{.3 + k * .55:.2f}s" dur=".55s" values="0;{f(seg_w)}" fill="freeze"/></rect>')
    y, step = 147.0, 20.5
    for i, (ind, k, v) in enumerate(YAML, 1):
        s.append(f'<text x="506" y="{f(y)}" text-anchor="end" fill="{t["muted"]}" opacity=".5" font-family="{MONO}" font-size="13">{i}</text>')
        if ind == 0:
            body = f'<tspan fill="{t["accent"]}" font-weight="700">{escape(k)}:</tspan>'
            x = 525
        else:
            body = f'<tspan fill="{t["key"]}">{escape(k)}: </tspan><tspan fill="{t["text"]}">{escape(v)}</tspan>'
            x = 542
        s.append(f'<g opacity="0"><animate attributeName="opacity" begin="{.15 + i * .07:.2f}s" dur=".35s" values="0;1" fill="freeze"/>'
                 f'<text x="{x}" y="{f(y)}" font-family="{MONO}" font-size="13">{body}</text></g>')
        y += step
    # cursor
    s.append(f'<rect x="525" y="{f(y - 14)}" width="8" height="17" fill="{t["accent"]}">'
             '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')
    # barra de estado de vim
    nbytes = sum(len(k) + len(v) + 4 for _, k, v in YAML)
    s.append(f'<path d="M474 526H1146" stroke="{t["line"]}"/>'
             f'<rect x="475" y="527" width="670" height="32" fill="{t["panel"]}"/>'
             f'<rect x="485" y="533" width="72" height="20" rx="3" fill="{t["accent"]}"/>'
             f'<text x="521" y="547" text-anchor="middle" fill="{t["panel"]}" font-family="{MONO}" font-size="11" font-weight="700">NORMAL</text>'
             f'<text x="569" y="547" fill="{t["text"]}" font-family="{MONO}" font-size="12" font-weight="600">driver.yml</text>'
             f'<text x="740" y="547" fill="{t["muted"]}" font-family="{MONO}" font-size="11">[utf-8]</text>'
             f'<circle cx="822" cy="543" r="4" fill="{t["green"]}"><animate attributeName="opacity" values="1;.3;1" dur="2s" repeatCount="indefinite"/></circle>'
             f'<text x="832" y="547" fill="{t["muted"]}" font-family="{MONO}" font-size="11">disponible</text>'
             f'<text x="1134" y="547" text-anchor="end" fill="{t["muted"]}" font-family="{MONO}" font-size="11">'
             f'{len(YAML)}L, {nbytes}B  100%  {len(YAML) + 1}:1</text>')
    body = "".join(s)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Maykol (Kmykh) — perfil animado: retrato en puntos y driver.yml">'
            f'<style>{font_css(body, (900,))}</style>{body}</svg>')


def main():
    if not PORTRAIT.exists():
        raise SystemExit(f"Falta la foto: {PORTRAIT}")
    for i, theme in enumerate(THEMES):
        rng = np.random.default_rng(SEED + i)
        portrait = portrait_points(theme, rng)
        logos = {n: {"travel": logo_points(n, TRAVELLERS, rng), "hold": logo_points(n, None, rng)} for n in LOGO_ORDER}
        out = OUT / f"banner-{theme}.svg"
        out.write_text(render(theme, portrait, logos, rng), encoding="utf-8")
        print(f"{out.relative_to(ROOT)}: {out.stat().st_size / 1024:.0f} KB · {len(portrait)} puntos")


if __name__ == "__main__":
    main()
