#!/usr/bin/env python3
"""
Generador de los SVG del perfil de GitHub de Kmykh (temática F1).

Cada pieza se genera en dos versiones (dark / light) para que el README
muestre la correcta según el tema de quien visita.

Uso:  pip install -r scripts/banner/requirements.txt
      python3 scripts/build.py      (desde la raíz del repo)
Edita PALETTE, los textos o los puntajes de los radares y vuelve a ejecutarlo.
"""
import math
from pathlib import Path
from xml.sax.saxutils import escape

from fonts import STACK as DISP, font_css

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

# ─────────────────────────── MARCA ───────────────────────────
# Carbono + rojo de carrera; púrpura / verde / amarillo como en los tiempos por sector.
PALETTE = {
    "dark": {
        "bg": "#0b0b0f", "surface": "#111116", "surface2": "#18181f",
        "border": "#272731", "text": "#f3f3f6", "muted": "#8d8d9a",
        "red": "#ff2a1f", "purple": "#b26bff", "green": "#2fdc6a",
        "yellow": "#ffcc1a", "blue": "#4d9bff", "lamp": "#2b1716",
    },
    "light": {
        "bg": "#ffffff", "surface": "#f8f8fa", "surface2": "#efeff3",
        "border": "#dcdce4", "text": "#111116", "muted": "#5e5e6c",
        "red": "#d81e10", "purple": "#7c3aed", "green": "#15803d",
        "yellow": "#b45309", "blue": "#1d4ed8", "lamp": "#ecdcda",
    },
}
SANS = "Inter,'Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

BASE_CSS = f"""
.sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}} .disp{{font-family:{DISP}}}
.in{{animation:in .7s cubic-bezier(.2,.8,.2,1) both}}
@keyframes in{{from{{opacity:0;transform:translateX(-10px)}}to{{opacity:1;transform:none}}}}
.caret{{animation:blink 1.1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.lit{{opacity:0;animation:lit 1s steps(1)}}
@keyframes lit{{0%,100%{{opacity:1}}}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 2s ease-out infinite}}
@keyframes pulse{{0%{{transform:scale(.6);opacity:.6}}100%{{transform:scale(2);opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def svg(w, h, body, label, css="", weights=(700, 900)):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" xml:space="preserve" role="img" aria-label="{escape(label)}">'
        f"<style>{font_css(body, weights)}{BASE_CSS}{css}</style>{body}</svg>"
    )


def card(w, h, c, rx=18, x=0, y=0):
    return (f'<rect x="{x+.5}" y="{y+.5}" width="{w-1}" height="{h-1}" rx="{rx}" '
            f'fill="{c["surface"]}" stroke="{c["border"]}"/>')


def stripes(c, x, y, n=3, color="red"):
    """Franjas inclinadas tipo librea, alineadas a la derecha en x."""
    return "".join(f'<path d="M{x - i*13 - 9} {y}h9l-8 16h-9z" fill="{c[color]}" opacity="{1 - i*.3:.1f}"/>'
                   for i in range(n))


def lights(c, x, y, r=6, step=19, t0=.25, gap=.3, out=1.9):
    """Semáforo de salida: se encienden de a uno y se apagan juntos (lights out)."""
    g = []
    for i in range(5):
        cx, d = x + i * step, t0 + i * gap
        g.append(f'<circle cx="{cx}" cy="{y}" r="{r}" fill="{c["lamp"]}"/>'
                 f'<circle class="lit" style="animation-delay:{d:.2f}s;animation-duration:{out - d:.2f}s" '
                 f'cx="{cx}" cy="{y}" r="{r}" fill="{c["red"]}"/>')
    return "".join(g)


def spans(segs, c):
    """[(texto, color_key), ...] -> tspans en una sola línea."""
    out, pend = [], ""
    for t, k in segs:
        if t.startswith("@") and k == "":
            pend = f' x="{t[1:]}"'; continue
        out.append(f'<tspan{pend} fill="{c[k]}">{escape(t)}</tspan>'); pend = ""
    return "".join(out)


def pill(c, x, y, txt, color="red", fs=11.5, solid=True):
    w = len(txt) * fs * .62 + 22
    bg = f'fill="{c[color]}"' if solid else f'fill="{c[color]}" fill-opacity=".12" stroke="{c[color]}"'
    fg = c["bg"] if solid else c[color]
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="22" rx="4" {bg}/>'
            f'<text x="{x + w/2:.1f}" y="{y + 15.5}" text-anchor="middle" class="disp" font-size="{fs}" '
            f'font-weight="900" letter-spacing="1" fill="{fg}">{escape(txt)}</text>'), w


def tags_row(c, x, y, tags, dot="red"):
    out = []
    for j, tag in enumerate(tags):
        w = len(tag) * 7.4 + (34 if j == 0 else 22)
        out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="24" rx="12" fill="{c["surface2"]}" stroke="{c["border"]}"/>')
        if j == 0:
            out.append(f'<circle cx="{x+13:.1f}" cy="{y+12}" r="4" fill="{c[dot]}"/>'
                       f'<text x="{x+23:.1f}" y="{y+16.5}" class="mono" font-size="12" fill="{c["text"]}">{escape(tag)}</text>')
        else:
            out.append(f'<text x="{x+11:.1f}" y="{y+16.5}" class="mono" font-size="12" fill="{c["muted"]}">{escape(tag)}</text>')
        x += w + 8
    return "".join(out)


def wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    return lines + [cur]


def save(name, theme, content):
    (OUT / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")


# ─────────────────────────── WHOAMI ───────────────────────────
DRIVER = {"code": "ROJ", "name": "MAYKOL ROJAS", "country": "PER", "team": "MindaCode"}


def driver_card(c, x, y, w, h):
    """Tarjeta de piloto al estilo de los gráficos de TV."""
    cx = x + 20
    b = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{c["surface2"]}" stroke="{c["border"]}"/>',
         f'<path d="M{x+12} {y}h{w-24}" stroke="{c["red"]}" stroke-width="3"/>',
         f'<text x="{cx}" y="{y+34}" class="mono" font-size="10.5" letter-spacing="2" fill="{c["muted"]}">PILOTO</text>',
         stripes(c, x + w - 16, y + 22),
         f'<text x="{cx-2}" y="{y+96}" class="disp" font-size="62" font-weight="900" font-style="italic" '
         f'letter-spacing="-1" fill="{c["text"]}">{DRIVER["code"]}</text>',
         f'<path d="M{cx} {y+108}h86l-5 6h-86z" fill="{c["red"]}"/>',
         f'<text x="{cx}" y="{y+140}" class="disp" font-size="16" font-weight="700" letter-spacing=".5" fill="{c["text"]}">{DRIVER["name"]}</text>',
         # bandera del Perú: rojo · blanco · rojo
         f'<g transform="translate({cx} {y+156})"><rect width="11" height="20" fill="#d91023"/>'
         f'<rect x="11" width="11" height="20" fill="#ffffff"/><rect x="22" width="11" height="20" fill="#d91023"/>'
         f'<rect x=".5" y=".5" width="32" height="19" fill="none" stroke="{c["border"]}"/></g>',
         f'<text x="{cx+44}" y="{y+171}" class="mono" font-size="12.5" fill="{c["muted"]}">{DRIVER["country"]} · Lima</text>',
         f'<path d="M{cx} {y+198}h{w-40}" stroke="{c["border"]}" stroke-dasharray="3 5"/>']
    rows = [("ESCUDERÍA", DRIVER["team"], "text"), ("LIDERA", "3 proyectos", "text"),
            ("ENFOQUE", "IA · Mobile", "text"), ("MÉTODO", "Scrum", "text")]
    for i, (k, v, col) in enumerate(rows):
        yy = y + 228 + i * 48
        b.append(f'<text x="{cx}" y="{yy}" class="mono" font-size="10.5" letter-spacing="1.5" fill="{c["muted"]}">{k}</text>'
                 f'<text x="{cx}" y="{yy+21}" class="disp" font-size="17" font-weight="700" fill="{c[col]}">{escape(v)}</text>')
    yb = y + h - 26
    b.append(f'<circle class="pulse" cx="{cx+5}" cy="{yb-4}" r="7" fill="{c["green"]}" opacity=".35"/>'
             f'<circle cx="{cx+5}" cy="{yb-4}" r="4" fill="{c["green"]}"/>'
             f'<text x="{cx+18}" y="{yb}" class="mono" font-size="12.5" fill="{c["green"]}">disponible</text>')
    return f'<g class="in" style="animation-delay:.4s">{"".join(b)}</g>'


def whoami(t):
    c = PALETTE[t]; W = 900
    P = [("kmykh", "red"), (" ~ ", "muted"), ("❯ ", "yellow")]
    def kv(k, v, last=False):
        return [("@48", ""), (k, "text"), ("@178", "")] + v + ([] if last else [(",", "muted")])
    s = lambda x: [(f'"{x}"', "yellow")]
    arr = lambda *xs: [("[", "muted")] + sum([s(x) + ([(", ", "muted")] if i < len(xs) - 1 else []) for i, x in enumerate(xs)], []) + [("]", "muted")]
    lines = [
        P + [("whoami --driver", "text")],
        [],
        [("const ", "red"), ("maykol", "text"), (" = {", "muted")],
        kv("rol:", s("Software Engineer · Mobile & IA")),
        kv("ahora:", s("IA en aplicaciones móviles")),
        kv("enfoque:", arr("proyectos con IA", "apps móviles", "aplicaciones")),
        kv("lidero:", arr("Aura Nova", "Aliada", "Vitalify")),
        kv("craft:", s("UX Design · centrado en el usuario")),
        kv("metodología:", arr("Scrum", "Agile")),
        kv("equipo:", s("Co-founder @ MindaCode")),
        kv("base:", s("Lima, Perú")),
        kv("disponible:", [("true", "purple")], last=True),
        [("};", "muted")],
        [],
        P + [("▍", "red")],
    ]
    y0, step = 92, 29; H = y0 + step * (len(lines) - 1) + 34
    body = [card(W, H, c, 16),
            f'<path d="M1 44h{W-2}" stroke="{c["border"]}"/>',
            lights(c, 26, 22),
            f'<text x="{W/2}" y="27" text-anchor="middle" class="mono" font-size="12.5" fill="{c["muted"]}">maykol@pitwall — zsh</text>',
            f'<text x="{W-24}" y="27" text-anchor="end" class="mono" font-size="11.5" fill="{c["muted"]}">LAP 01</text>']
    for i, segs in enumerate(lines):
        if not segs: continue
        cls = ' class="caret"' if segs[-1][0] == "▍" else ""
        inner = (spans(segs[:-1], c) + f'<tspan{cls} fill="{c["red"]}">▍</tspan>') if cls else spans(segs, c)
        body.append(f'<g class="in" style="animation-delay:{.2+i*.12:.2f}s"><text x="32" y="{y0+i*step}" class="mono" font-size="15">{inner}</text></g>')
    body.append(driver_card(c, 712, 64, 164, H - 84))
    save("whoami", t, svg(W, H, "".join(body), "Terminal: whoami de Maykol, con tarjeta de piloto"))


# ─────────────────────────── ESCUDERÍAS (proyectos que lidero) ───────────────────────────
LEADS = [
    ("01", "Aura Nova", "E-commerce oficial de Aura Nova, tienda de detalles. Desarrollo y lidero la plataforma.",
     ["e-commerce", "negocio"], "purple"),
    ("02", "Aliada", "Lidero el desarrollo del proyecto y coordino al equipo de punta a punta.",
     ["liderazgo", "equipo"], "green"),
    ("03", "Vitalify", "Salud digital: monitoreo de signos vitales. Lidero el desarrollo.",
     ["salud", "IoT"], "red"),
]


def leads(t):
    c = PALETTE[t]; W, H = 900, 250; cw, gap = 284, 24
    body = []
    for i, (num, name, desc, tags, col) in enumerate(LEADS):
        x = i * (cw + gap)
        b = [card(cw, H - 2, c, 14, x, 1),
             f'<path d="M{x+14} 1.5h{cw-28}" stroke="{c[col]}" stroke-width="3"/>',
             f'<text x="{x+22}" y="62" class="disp" font-size="46" font-weight="900" font-style="italic" fill="{c[col]}">{num}</text>']
        p, pw = pill(c, 0, 26, "LÍDER")
        b.append(f'<g transform="translate({x + cw - 22 - pw:.1f} 0)">{p}</g>')
        b.append(f'<text x="{x+22}" y="104" class="disp" font-size="27" font-weight="700" fill="{c["text"]}">{escape(name)}</text>')
        for j, line in enumerate(wrap(desc, 33)[:3]):
            b.append(f'<text x="{x+22}" y="{134+j*20}" class="sans" font-size="14" fill="{c["muted"]}">{escape(line)}</text>')
        b.append(tags_row(c, x + 22, H - 46, tags, col))
        body.append(f'<g class="in" style="animation-delay:{.1+i*.15:.2f}s">{"".join(b)}</g>')
    save("leads", t, svg(W, H, "".join(body), "Proyectos que lidero: Aura Nova, Aliada y Vitalify"))


# ─────────────────────────── SETUP (stack) ───────────────────────────
# Solo lenguajes de programación en "lenguajes" (HTML/CSS no lo son).
STACK = [
    ("lenguajes", ["Dart", "TypeScript", "JavaScript", "Java", "C#", "SQL"]),
    ("mobile",    ["Flutter", "Android", "iOS"]),
    ("ia",        ["LLMs en apps", "APIs de IA", "prompt engineering"]),
    ("web",       ["React", "Next.js", "Spring Boot", "ASP.NET Core"]),
    ("datos",     ["PostgreSQL", "Supabase"]),
    ("ux / ui",   ["Figma", "UX Design", "prototipado"]),
    ("método",    ["Scrum", "Agile", "Git"]),
    ("extra",     ["Docker", "ESP32", "Unity"]),
]
TYRES = ["red", "yellow", "text", "green", "blue"]  # blando · medio · duro · intermedio · lluvia


def stack(t):
    c = PALETTE[t]; W = 900; y0, step = 82, 32
    H = y0 + step * len(STACK) + 58
    body = [card(W, H, c, 16),
            f'<g class="in"><text x="32" y="46" class="mono" font-size="15">'
            f'{spans([("maykol", "red"), ("@", "muted"), ("pitwall", "text"), ("   setup.json", "muted")], c)}</text></g>',
            f'<text x="{W-70}" y="46" text-anchor="end" class="disp" font-size="13" font-weight="700" letter-spacing="2" fill="{c["muted"]}">SETUP · 2026</text>',
            stripes(c, W - 28, 33)]
    for i, (k, vals) in enumerate(STACK):
        y = y0 + i * step + 8
        tyre = c[TYRES[i % len(TYRES)]]
        segs = [(k, "text"), ("@178", "")]
        for j, v in enumerate(vals):
            segs.append((v, "red" if j == 0 else "text"))
            if j < len(vals) - 1: segs.append(("  ·  ", "muted"))
        body.append(f'<g class="in" style="animation-delay:{.15+i*.08:.2f}s">'
                    f'<circle cx="40" cy="{y-5}" r="7" fill="{c["surface"]}" stroke="{tyre}" stroke-width="3.5"/>'
                    f'<text x="60" y="{y}" class="mono" font-size="15">{spans(segs, c)}</text></g>')
    fy = H - 24
    body.append(f'<path d="M24 {fy-26}h{W-48}" stroke="{c["border"]}" stroke-dasharray="3 5"/>')
    body.append(f'<g class="in" style="animation-delay:.9s"><text x="32" y="{fy}" class="mono" font-size="13.5">'
                f'{spans([("status: ", "muted"), ("listo para la parrilla", "green"), ("   ·   método: ", "muted"), ("Scrum", "text"), ("   ·   ", "muted"), ("open to work", "red")], c)}</text></g>')
    save("stack", t, svg(W, H, "".join(body), "Stack tecnológico de Maykol (setup del monoplaza)"))


# ─────────────────────────── TELEMETRÍA (radares) ───────────────────────────
# Puntajes 0-100: ajústalos a tu criterio.
RADARS = {
    "radar-skills": ("telemetry --skills", "habilidades", [
        ("IA aplicada", 78), ("Mobile", 88), ("UX Design", 84),
        ("Liderazgo", 85), ("Backend", 78), ("Scrum", 82)]),
    "radar-langs": ("telemetry --langs", "lenguajes", [
        ("Dart", 70), ("TypeScript", 80), ("JavaScript", 85),
        ("Java", 75), ("C#", 75), ("SQL", 78)]),
}


def radar(t, name):
    c = PALETTE[t]; W, H = 440, 420; cx, cy, R = 220, 232, 112
    title, sub, data = RADARS[name]; n = len(data)
    pt = lambda i, r: (cx + r * math.sin(2 * math.pi * i / n), cy - r * math.cos(2 * math.pi * i / n))
    body = [card(W, H, c, 16),
            f'<text x="24" y="38" class="mono" font-size="13.5">{spans([("$ ", "red"), (title, "text")], c)}</text>',
            f'<circle class="pulse" cx="{W-38-len(sub)*7.6:.0f}" cy="34" r="6" fill="{c["red"]}" opacity=".35"/>'
            f'<circle cx="{W-38-len(sub)*7.6:.0f}" cy="34" r="3.5" fill="{c["red"]}"/>',
            f'<text x="{W-24}" y="38" text-anchor="end" class="mono" font-size="12.5" fill="{c["muted"]}">{sub}</text>']
    for f in (.25, .5, .75, 1):
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, R * f) for i in range(n)))
        dash = ' stroke-dasharray="3 4"' if f < 1 else ""
        body.append(f'<polygon points="{poly}" fill="none" stroke="{c["border"]}"{dash}/>')
    for i in range(n):
        x, y = pt(i, R); body.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{c["border"]}"/>')
    rel = [(R * v / 100 * math.sin(2 * math.pi * i / n), -R * v / 100 * math.cos(2 * math.pi * i / n)) for i, (_, v) in enumerate(data)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in rel)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{c["surface"]}" stroke="{c["red"]}" stroke-width="2.5"/>' for x, y in rel)
    body.append(f'<g transform="translate({cx} {cy})"><g class="grow">'
                f'<polygon points="{poly}" fill="{c["red"]}" fill-opacity=".14" stroke="{c["red"]}" stroke-width="2.5" stroke-linejoin="round"/>{dots}</g></g>')
    for i, (label, v) in enumerate(data):
        x, y = pt(i, R + 22)
        anchor = "middle" if abs(x - cx) < 5 else ("start" if x > cx else "end")
        dy = -18 if y < cy - R * .9 else (12 if y > cy + R * .9 else -2)
        body.append(f'<text x="{x:.1f}" y="{y+dy:.1f}" text-anchor="{anchor}" class="disp" font-size="14" font-weight="700" fill="{c["text"]}">{escape(label)}'
                    f'<tspan x="{x:.1f}" dy="17" class="mono" font-size="12" font-weight="400" fill="{c["muted"]}">{v}</tspan></text>')
    css = """.grow{animation:grow 1.2s cubic-bezier(.2,.8,.2,1) .3s both}
    @keyframes grow{from{transform:scale(0);opacity:0}to{transform:scale(1);opacity:1}}"""
    save(name, t, svg(W, H, "".join(body), f"Telemetría de {sub}", css, weights=(700,)))


# ─────────────────────────── PARRILLA (proyectos públicos) ───────────────────────────
PROJECTS = [
    ("AppMovil-VacApp", "App móvil personal para la gestión de vacas.", ["Flutter", "Dart"]),
    ("AccesiTour", "Plataforma autónoma para personas con discapacidad en entornos arqueológicos.", ["TypeScript", "accesibilidad"]),
    ("Page-Mindacode", "Web de la startup MindaCode, donde soy co-founder.", ["TypeScript", "web"]),
    ("VideoGame-MaskInThePit", "Videojuego 2D sobre la locura como estrés. Capítulo 1.", ["Unity", "C#"]),
    ("Page-Transportify", "Landing page para una empresa de transporte.", ["web", "landing"]),
    ("Page-Donfy", "Página web del proyecto Donfy.", ["web", "landing"]),
]


def project(t, i, name, desc, tags):
    """Tarjeta en la parrilla: las posiciones pares salen un poco más atrás, como en la salida."""
    c = PALETTE[t]; W, H, CH = 440, 184, 166
    y = 0 if i % 2 == 0 else H - CH
    pos = f"P{i+1}"
    b = [card(W, CH, c, 14, 0, y),
         f'<path d="M1 {y+14}v{CH-28}" stroke="{c["red"] if i == 0 else c["border"]}" stroke-width="3"/>',
         f'<text x="22" y="{y+44}" class="disp" font-size="26" font-weight="900" font-style="italic" fill="{c["red"] if i == 0 else c["muted"]}">{pos}</text>',
         f'<text x="74" y="{y+42}" class="disp" font-size="19" font-weight="700" fill="{c["text"]}">{escape(name)}</text>',
         f'<text x="{W-24}" y="{y+42}" text-anchor="end" class="sans" font-size="18" fill="{c["red"]}">↗</text>']
    for j, line in enumerate(wrap(desc, 46)[:2]):
        b.append(f'<text x="74" y="{y+72+j*20}" class="sans" font-size="14" fill="{c["muted"]}">{escape(line)}</text>')
    b.append(tags_row(c, 74, y + CH - 42, tags))
    body = f'<g class="in" style="animation-delay:{.1+i*.08:.2f}s">{"".join(b)}</g>'
    save(f"project-{name.lower()}", t, svg(W, H, body, f"{pos}: proyecto {name}"))


# ─────────────────────────── BANDERA A CUADROS (cierre) ───────────────────────────
def finish(t):
    c = PALETTE[t]; W, H, q = 900, 132, 12
    body = [f'''<defs>
      <pattern id="chk" width="{2*q}" height="{2*q}" patternUnits="userSpaceOnUse">
        <rect width="{2*q}" height="{2*q}" fill="{c["bg"]}"/>
        <rect width="{q}" height="{q}" fill="{c["text"]}"/><rect x="{q}" y="{q}" width="{q}" height="{q}" fill="{c["text"]}"/>
        <animateTransform attributeName="patternTransform" type="translate" from="0 0" to="{2*q} 0" dur="1.6s" repeatCount="indefinite"/>
      </pattern>
      <linearGradient id="fade" x1="0" x2="1">
        <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".2" stop-color="#fff" stop-opacity="1"/>
        <stop offset=".8" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask></defs>''',
            f'<rect y="8" width="{W}" height="{2*q}" fill="url(#chk)" mask="url(#m)"/>',
            f'<text x="{W/2}" y="78" text-anchor="middle" class="disp" font-size="30" font-weight="900" font-style="italic" '
            f'letter-spacing="1" fill="{c["text"]}">GRACIAS POR LA VISITA</text>',
            f'<path d="M{W/2-40} 92h80l-4 5h-80z" fill="{c["red"]}"/>',
            f'<text x="{W/2}" y="122" text-anchor="middle" class="mono" font-size="13" fill="{c["muted"]}">'
            f'box, box · nos vemos en la próxima vuelta · Lima, Perú</text>']
    save("finish", t, svg(W, H, "".join(body), "Bandera a cuadros: gracias por la visita", weights=(900,)))


# ─────────────────────────── BUILD ───────────────────────────
if __name__ == "__main__":
    for t in PALETTE:
        whoami(t); leads(t); stack(t); finish(t)  # el banner lo genera scripts/banner/generate.py
        for r in RADARS: radar(t, r)
        for i, p in enumerate(PROJECTS): project(t, i, *p)
    print(f"SVGs generados en {OUT}")
