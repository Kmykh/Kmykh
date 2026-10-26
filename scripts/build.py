#!/usr/bin/env python3
"""
Generador de los SVG del perfil de GitHub de Kmykh.

Cada pieza se genera en dos versiones (dark / light) para que el README
muestre la correcta según el tema de quien visita.

Uso:  python3 scripts/build.py      (desde la raíz del repo)
Edita PALETTE, los textos o los puntajes de los radares y vuelve a ejecutarlo.
"""
import math
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

# ─────────────────────────── MARCA ───────────────────────────
PALETTE = {
    "dark": {
        "bg": "#0c0f0d", "surface": "#121815", "surface2": "#18201b",
        "border": "#243029", "text": "#eef3ef", "muted": "#8b968f",
        "green": "#22c55e", "orange": "#f97316",
    },
    "light": {
        "bg": "#ffffff", "surface": "#f7f9f7", "surface2": "#eef3ef",
        "border": "#dde5df", "text": "#0f1411", "muted": "#5b6660",
        "green": "#15803d", "orange": "#ea580c",
    },
}
SANS = "Inter,'Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

BASE_CSS = f"""
.sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}}
.in{{animation:in .7s cubic-bezier(.2,.8,.2,1) both}}
@keyframes in{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
.caret{{animation:blink 1.1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def svg(w, h, body, label, css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" xml:space="preserve" role="img" aria-label="{escape(label)}">'
        f"<style>{BASE_CSS}{css}</style>{body}</svg>"
    )


def card(w, h, c, rx=18):
    return (f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="{rx}" '
            f'fill="{c["surface"]}" stroke="{c["border"]}"/>')


def spans(segs, c):
    """[(texto, color_key), ...] -> tspans en una sola línea."""
    out, pend = [], ""
    for t, k in segs:
        if t.startswith("@") and k == "":
            pend = f' x="{t[1:]}"'; continue
        out.append(f'<tspan{pend} fill="{c[k]}">{escape(t)}</tspan>'); pend = ""
    return "".join(out)


def save(name, theme, content):
    (OUT / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")


# ─────────────────────────── BANNER ───────────────────────────
def banner(t):
    c = PALETTE[t]; W, H = 1000, 250
    chips = [("●", "Disponible para proyectos"), ("", "Co-founder @ MindaCode"), ("", "Lima, Perú")]
    body = [card(W, H, c, 22)]
    body.append(f'''<defs>
      <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
        <circle cx="2" cy="2" r="1.3" fill="{c["border"]}"/></pattern>
      <radialGradient id="fade" cx="50%" cy="50%" r="60%">
        <stop offset="0" stop-color="#fff" stop-opacity="0"/>
        <stop offset="1" stop-color="#fff" stop-opacity="1"/></radialGradient>
      <mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask></defs>
      <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22" fill="url(#dots)" mask="url(#m)"/>''')
    body.append(f'<g class="in" style="animation-delay:.1s"><text x="500" y="58" text-anchor="middle" class="mono" font-size="15">'
                f'<tspan fill="{c["green"]}">~/kmykh</tspan><tspan fill="{c["muted"]}"> — software engineer</tspan></text></g>')
    body.append(f'<g class="in" style="animation-delay:.25s"><text x="500" y="122" text-anchor="middle" class="sans" '
                f'font-size="58" font-weight="700" letter-spacing="-1.5" fill="{c["text"]}">Maykol</text></g>')
    body.append(f'<rect class="bar" x="470" y="138" width="60" height="3" rx="1.5" fill="{c["green"]}"/>')
    body.append(f'<g class="in" style="animation-delay:.45s"><text x="500" y="174" text-anchor="middle" class="sans" '
                f'font-size="20" fill="{c["muted"]}">Diseño y desarrollo webs animadas, rápidas y que convierten.</text></g>')
    # chips centrados
    widths = [len(txt) * 7.6 + (44 if dot else 30) for dot, txt in chips]
    gap = 10; x = (W - (sum(widths) + gap * (len(chips) - 1))) / 2
    for i, ((dot, txt), w) in enumerate(zip(chips, widths)):
        g = [f'<rect x="{x:.1f}" y="196" width="{w:.1f}" height="30" rx="15" fill="{c["surface2"]}" stroke="{c["border"]}"/>']
        tx = x + 15
        if dot:
            g.append(f'<circle class="pulse" cx="{x+17:.1f}" cy="211" r="8" fill="{c["orange"]}" opacity=".35"/>'
                     f'<circle cx="{x+17:.1f}" cy="211" r="4" fill="{c["orange"]}"/>')
            tx = x + 30
        g.append(f'<text x="{tx:.1f}" y="216" class="sans" font-size="13.5" fill="{c["text"]}">{escape(txt)}</text>')
        body.append(f'<g class="in" style="animation-delay:{.6+i*.12:.2f}s">{"".join(g)}</g>')
        x += w + gap
    css = """.bar{transform-origin:500px 0;animation:bar 1s cubic-bezier(.2,.8,.2,1) .5s both}
    @keyframes bar{from{transform:scaleX(0)}to{transform:scaleX(1)}}
    .pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2s ease-out infinite}
    @keyframes pulse{0%{transform:scale(.6);opacity:.6}100%{transform:scale(1.8);opacity:0}}"""
    save("banner", t, svg(W, H, "".join(body), "Maykol — Kmykh, software engineer", css))


# ─────────────────────────── WHOAMI ───────────────────────────
def whoami(t):
    c = PALETTE[t]; W = 900
    P = [("kmykh", "green"), (" ~ ", "muted"), ("❯ ", "orange")]
    def kv(k, v, last=False):
        return [("@48", ""), (k, "text"), ("@192", "")] + v + ([] if last else [(",", "muted")])
    s = lambda x: [(f'"{x}"', "green")]
    arr = lambda *xs: [("[", "muted")] + sum([s(x) + ([(", ", "muted")] if i < len(xs) - 1 else []) for i, x in enumerate(xs)], []) + [("]", "muted")]
    lines = [
        P + [("whoami", "text")],
        [],
        [("const ", "orange"), ("maykol", "text"), (" = {", "muted")],
        kv("rol:", s("Software Engineer · Web Developer")),
        kv("ahora:", arr("Co-founder @ MindaCode", "Tesis: Vitalify")),
        kv("base:", s("Lima, Perú")),
        kv("construyo:", arr("webs animadas", "apps", "backends")),
        kv("enfoque:", s("motion fluido + rendimiento real")),
        kv("disponible:", [("true", "orange")], last=True),
        [("};", "muted")],
        [],
        P + [("▍", "orange")],
    ]
    y0, step = 92, 29; H = y0 + step * (len(lines) - 1) + 34
    body = [card(W, H, c, 16),
            f'<path d="M1 44h{W-2}" stroke="{c["border"]}"/>',
            *[f'<circle cx="{26+i*20}" cy="22" r="6" fill="{c["border"]}"/>' for i in range(3)],
            f'<text x="{W/2}" y="27" text-anchor="middle" class="mono" font-size="12.5" fill="{c["muted"]}">maykol@kmykh — zsh</text>']
    for i, segs in enumerate(lines):
        if not segs: continue
        cls = ' class="caret"' if segs[-1][0] == "▍" else ""
        inner = (spans(segs[:-1], c) + f'<tspan{cls} fill="{c["orange"]}">▍</tspan>') if cls else spans(segs, c)
        body.append(f'<g class="in" style="animation-delay:{.2+i*.18:.2f}s"><text x="32" y="{y0+i*step}" class="mono" font-size="15.5">{inner}</text></g>')
    save("whoami", t, svg(W, H, "".join(body), "Terminal: whoami de Maykol"))


# ─────────────────────────── STACK ───────────────────────────
STACK = [
    ("frontend", ["React", "TypeScript", "JavaScript", "HTML", "CSS"]),
    ("motion",   ["CSS animations", "scroll effects", "micro-interacciones"]),
    ("backend",  ["Java · Spring Boot", "ASP.NET Core (.NET 8)"]),
    ("mobile",   ["Flutter", "Dart"]),
    ("data",     ["PostgreSQL", "Supabase", "SQL"]),
    ("iot",      ["ESP32", "MQTT"]),
    ("gamedev",  ["Unity", "C#"]),
]

def stack(t):
    c = PALETTE[t]; W = 900; y0, step = 78, 31
    H = y0 + step * len(STACK) + 62
    body = [card(W, H, c, 16),
            f'<g class="in"><text x="32" y="46" class="mono" font-size="15.5">'
            f'{spans([("maykol", "green"), ("@", "muted"), ("stack", "text"), ("   package.json", "muted")], c)}</text></g>']
    for i, (k, vals) in enumerate(STACK):
        branch = "╰─ " if i == len(STACK) - 1 else "├─ "
        segs = [(branch, "muted"), (k, "text"), ("@150", "")]
        for j, v in enumerate(vals):
            segs.append((v, "green" if j == 0 else "text"))
            if j < len(vals) - 1: segs.append(("  ·  ", "muted"))
        body.append(f'<g class="in" style="animation-delay:{.15+i*.1:.2f}s"><text x="32" y="{y0+i*step+8}" class="mono" font-size="15">{spans(segs, c)}</text></g>')
    fy = H - 26
    body.append(f'<path d="M24 {fy-26}h{W-48}" stroke="{c["border"]}" stroke-dasharray="3 5"/>')
    body.append(f'<g class="in" style="animation-delay:1s"><text x="32" y="{fy}" class="mono" font-size="13.5">'
                f'{spans([("status: ", "muted"), ("ready", "green"), ("   ·   arquitectura: ", "muted"), ("hexagonal · REST", "text"), ("   ·   ", "muted"), ("open to work", "orange")], c)}</text></g>')
    save("stack", t, svg(W, H, "".join(body), "Stack tecnológico de Maykol"))


# ─────────────────────────── RADARES ───────────────────────────
# Puntajes 0-100: ajústalos a tu criterio.
RADARS = {
    "radar-skills": ("skills.radar", "habilidades", [
        ("Animación", 85), ("Rendimiento", 82), ("UI / UX", 80),
        ("Responsive", 90), ("Backend", 75), ("Arquitectura", 72)]),
    "radar-langs": ("langs.radar", "lenguajes", [
        ("TypeScript", 80), ("JavaScript", 85), ("Java", 75),
        ("C#", 75), ("Dart", 70), ("SQL", 78)]),
}

def radar(t, name):
    c = PALETTE[t]; W, H = 440, 420; cx, cy, R = 220, 232, 112
    title, sub, data = RADARS[name]; n = len(data)
    pt = lambda i, r: (cx + r * math.sin(2 * math.pi * i / n), cy - r * math.cos(2 * math.pi * i / n))
    body = [card(W, H, c, 16),
            f'<text x="24" y="38" class="mono" font-size="13.5">{spans([("$ ", "orange"), (title, "text")], c)}</text>',
            f'<text x="{W-24}" y="38" text-anchor="end" class="mono" font-size="12.5" fill="{c["muted"]}">{sub}</text>']
    for f in (.25, .5, .75, 1):
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, R * f) for i in range(n)))
        body.append(f'<polygon points="{poly}" fill="none" stroke="{c["border"]}"/>')
    for i in range(n):
        x, y = pt(i, R); body.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{c["border"]}"/>')
    rel = [(R * v / 100 * math.sin(2 * math.pi * i / n), -R * v / 100 * math.cos(2 * math.pi * i / n)) for i, (_, v) in enumerate(data)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in rel)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{c["orange"]}"/>' for x, y in rel)
    body.append(f'<g transform="translate({cx} {cy})"><g class="grow">'
                f'<polygon points="{poly}" fill="{c["green"]}" fill-opacity=".16" stroke="{c["green"]}" stroke-width="2" stroke-linejoin="round"/>{dots}</g></g>')
    for i, (label, v) in enumerate(data):
        x, y = pt(i, R + 22)
        anchor = "middle" if abs(x - cx) < 5 else ("start" if x > cx else "end")
        dy = -18 if y < cy - R * .9 else (12 if y > cy + R * .9 else -2)
        body.append(f'<text x="{x:.1f}" y="{y+dy:.1f}" text-anchor="{anchor}" class="sans" font-size="13" fill="{c["text"]}">{escape(label)}'
                    f'<tspan x="{x:.1f}" dy="17" class="mono" font-size="12" fill="{c["muted"]}">{v}</tspan></text>')
    css = """.grow{animation:grow 1.2s cubic-bezier(.2,.8,.2,1) .3s both}
    @keyframes grow{from{transform:scale(0);opacity:0}to{transform:scale(1);opacity:1}}"""
    save(name, t, svg(W, H, "".join(body), f"Radar de {sub}", css))


# ─────────────────────────── ARQUITECTURAS ───────────────────────────
def box(c, x, y, w, h, title, sub, accent=False):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{c["surface2"]}" '
            f'stroke="{c["green"] if accent else c["border"]}"/>'
            f'<text x="{x+16}" y="{y+30}" class="sans" font-size="15" font-weight="600" fill="{c["text"]}">{escape(title)}</text>'
            f'<text x="{x+16}" y="{y+52}" class="mono" font-size="12" fill="{c["muted"]}">{escape(sub)}</text>')

def flow(c, d, label=None, lx=0, ly=0, delay=0):
    s = (f'<path d="{d}" fill="none" stroke="{c["border"]}" stroke-width="2"/>'
         f'<path class="flow" style="animation-delay:{delay}s" d="{d}" fill="none" stroke="{c["green"]}" '
         f'stroke-width="2" stroke-dasharray="6 10" marker-end="url(#ar)"/>')
    if label:
        s += f'<text x="{lx}" y="{ly}" text-anchor="middle" class="mono" font-size="11.5" fill="{c["orange"]}">{escape(label)}</text>'
    return s

FLOW_CSS = """.flow{animation:flow 1.2s linear infinite}
@keyframes flow{from{stroke-dashoffset:32}to{stroke-dashoffset:0}}"""

def arch_head(c, W, cmd, note):
    return (f'<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path d="M0 0L10 5L0 10z" fill="{c["green"]}"/></marker></defs>'
            f'<text x="28" y="40" class="mono" font-size="14">{spans([("$ ", "orange"), (cmd, "text")], c)}</text>'
            f'<text x="{W-28}" y="40" text-anchor="end" class="mono" font-size="12.5" fill="{c["muted"]}">{escape(note)}</text>')

def hexagon(cx, cy, r):
    return " ".join(f"{cx + r*math.cos(math.pi/3*i):.1f},{cy + r*math.sin(math.pi/3*i):.1f}" for i in range(6))

def arch_vitalify(t):
    c = PALETTE[t]; W, H = 900, 340
    b = [card(W, H, c, 16), arch_head(c, W, "tree ./vitalify", "tesis · IoMT · en desarrollo")]
    b.append(box(c, 28, 145, 192, 74, "Wearable", "ESP32 · signos vitales"))
    # núcleo hexagonal
    b.append(f'<rect x="268" y="70" width="330" height="236" rx="14" fill="none" stroke="{c["border"]}" stroke-dasharray="4 5"/>'
             f'<text x="284" y="98" class="sans" font-size="15" font-weight="600" fill="{c["text"]}">API · ASP.NET Core .NET 8</text>'
             f'<text x="284" y="118" class="mono" font-size="12" fill="{c["muted"]}">arquitectura hexagonal</text>')
    b.append(f'<polygon points="{hexagon(433, 205, 70)}" fill="{c["green"]}" fill-opacity=".09" stroke="{c["green"]}" stroke-width="1.5"/>'
             f'<text x="433" y="201" text-anchor="middle" class="sans" font-size="15" font-weight="600" fill="{c["text"]}">Dominio</text>'
             f'<text x="433" y="221" text-anchor="middle" class="mono" font-size="11.5" fill="{c["muted"]}">NEWS2 · MEWS</text>')
    b.append(f'<text x="316" y="210" text-anchor="middle" class="mono" font-size="11" fill="{c["muted"]}">puertos</text>'
             f'<text x="316" y="224" text-anchor="middle" class="mono" font-size="11" fill="{c["muted"]}">entrada</text>'
             f'<text x="550" y="210" text-anchor="middle" class="mono" font-size="11" fill="{c["muted"]}">puertos</text>'
             f'<text x="550" y="224" text-anchor="middle" class="mono" font-size="11" fill="{c["muted"]}">salida</text>')
    b.append(box(c, 668, 62, 204, 70, "PostgreSQL", "Supabase · TimescaleDB"))
    b.append(box(c, 668, 152, 204, 70, "App enfermería", "Flutter · alertas"))
    b.append(box(c, 668, 242, 204, 70, "Dashboard médico", "React"))
    b.append(flow(c, "M220 182H262", "MQTT", 241, 172, 0))
    b.append(flow(c, "M598 150C630 150 630 97 662 97", delay=.2))
    b.append(flow(c, "M598 187H662", delay=.4))
    b.append(flow(c, "M598 224C630 224 630 277 662 277", delay=.6))
    save("arch-vitalify", t, svg(W, H, "".join(b), "Arquitectura de Vitalify", FLOW_CSS))

def arch_vacty(t):
    c = PALETTE[t]; W, H = 900, 300
    b = [card(W, H, c, 16), arch_head(c, W, "tree ./vacty", "IoT · cadena de frío · en equipo")]
    b.append(box(c, 28, 130, 186, 74, "Sensor IoT", "ESP32 WROVER · DHT22"))
    b.append(f'<rect x="300" y="100" width="270" height="134" rx="12" fill="{c["surface2"]}" stroke="{c["green"]}"/>'
             f'<text x="318" y="132" class="sans" font-size="15" font-weight="600" fill="{c["text"]}">Backend REST</text>'
             f'<text x="318" y="156" class="mono" font-size="12" fill="{c["muted"]}">motor de alertas</text>'
             f'<text x="318" y="174" class="mono" font-size="12" fill="{c["muted"]}">por tipo de vacuna</text>'
             f'<text x="318" y="208" class="mono" font-size="12">{spans([("● ", "orange"), ("temperatura · vencimientos", "text")], c)}</text>')
    b.append(box(c, 648, 70, 224, 70, "Supabase", "PostgreSQL"))
    b.append(box(c, 648, 190, 224, 70, "App enfermera", "alertas · vencimientos · QR"))
    b.append(flow(c, "M214 167H294", "°C · %HR", 254, 157, 0))
    b.append(flow(c, "M570 140C606 140 606 105 642 105", delay=.25))
    b.append(flow(c, "M570 194C606 194 606 225 642 225", delay=.5))
    save("arch-vacty", t, svg(W, H, "".join(b), "Arquitectura de VacTy", FLOW_CSS))


# ─────────────────────────── PROYECTOS ───────────────────────────
PROJECTS = [
    ("Page-Mindacode", "Web de la startup MindaCode, donde soy co-founder.", ["TypeScript", "web"]),
    ("Page-Transportify", "Landing page para una empresa de transporte.", ["CSS", "landing"]),
    ("Page-Donfy", "Página web del proyecto Donfy.", ["CSS", "web"]),
    ("AccesiTour", "Plataforma autónoma para personas con discapacidad en entornos arqueológicos.", ["TypeScript", "a11y"]),
    ("AppMovil-VacApp", "Proyecto personal de gestión de vacas.", ["Dart", "Flutter"]),
    ("VideoGame-MaskInThePit", "Videojuego 2D sobre la locura como estrés. Capítulo 1.", ["C#", "Unity"]),
]

def wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    return lines + [cur]

def project(t, i, name, desc, tags):
    c = PALETTE[t]; W, H = 440, 168
    b = [card(W, H, c, 14),
         f'<text x="24" y="42" class="sans" font-size="18" font-weight="650" fill="{c["text"]}">{escape(name)}</text>',
         f'<text x="{W-24}" y="42" text-anchor="end" class="sans" font-size="18" fill="{c["orange"]}">↗</text>']
    for j, line in enumerate(wrap(desc, 50)[:2]):
        b.append(f'<text x="24" y="{74+j*21}" class="sans" font-size="14" fill="{c["muted"]}">{escape(line)}</text>')
    x = 24
    for j, tag in enumerate(tags):
        w = len(tag) * 7.4 + (34 if j == 0 else 22)
        b.append(f'<rect x="{x}" y="124" width="{w:.1f}" height="24" rx="12" fill="{c["surface2"]}" stroke="{c["border"]}"/>')
        if j == 0:
            b.append(f'<circle cx="{x+13}" cy="136" r="4" fill="{c["green"]}"/>'
                     f'<text x="{x+23}" y="140.5" class="mono" font-size="12" fill="{c["text"]}">{escape(tag)}</text>')
        else:
            b.append(f'<text x="{x+11}" y="140.5" class="mono" font-size="12" fill="{c["muted"]}">{escape(tag)}</text>')
        x += w + 8
    body = f'<g class="in" style="animation-delay:{.1+i*.08:.2f}s">{"".join(b)}</g>'
    save(f"project-{name.lower()}", t, svg(W, H, body, f"Proyecto {name}"))


# ─────────────────────────── BUILD ───────────────────────────
if __name__ == "__main__":
    for t in PALETTE:
        whoami(t); stack(t)  # el banner lo genera scripts/banner/generate.py
        for r in RADARS: radar(t, r)
        arch_vitalify(t); arch_vacty(t)
        for i, p in enumerate(PROJECTS): project(t, i, *p)
    print(f"SVGs generados en {OUT}")
