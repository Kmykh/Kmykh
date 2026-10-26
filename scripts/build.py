#!/usr/bin/env python3
"""
Generador de los SVG del perfil de GitHub de Kmykh.

Cada pieza se genera en dos versiones (dark / light) para que el README
muestre la correcta según el tema de quien visita.

Uso:  pip install -r scripts/banner/requirements.txt
      python3 scripts/build.py      (desde la raíz del repo)
Edita PALETTE, los textos o los puntajes de los radares y vuelve a ejecutarlo.
"""
import math
from pathlib import Path
from xml.sax.saxutils import escape

from fonts import STACK as DISP, font_css, text_width

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

# ─────────────────────────── MARCA ───────────────────────────
# Verde + naranja. En claro: tonos más profundos para que el texto se lea bien
# y fondos teñidos suaves ("tint") para chips y rellenos.
PALETTE = {
    "dark": {
        "bg": "#0c0f0d", "surface": "#111613", "surface2": "#171e1a",
        "border": "#25302a", "text": "#eef3ef", "muted": "#8b968f",
        "green": "#22c55e", "orange": "#f97316",
        "gtint": "#123321", "otint": "#3a2010",
    },
    "light": {
        "bg": "#ffffff", "surface": "#fafcfa", "surface2": "#f1f6f2",
        "border": "#dde7e0", "text": "#16231c", "muted": "#5f6f66",
        "green": "#178244", "orange": "#bf530a",
        "gtint": "#e6f4ea", "otint": "#fdeee2",
    },
}
TINT = {"green": "gtint", "orange": "otint"}
SANS = "Inter,'Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

BASE_CSS = f"""
.sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}} .disp{{font-family:{DISP}}}
.in{{animation:in .7s cubic-bezier(.2,.8,.2,1) both}}
@keyframes in{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
.caret{{animation:blink 1.1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 2s ease-out infinite}}
@keyframes pulse{{0%{{transform:scale(.6);opacity:.6}}100%{{transform:scale(2);opacity:0}}}}
.draw{{animation:draw 1.1s cubic-bezier(.2,.8,.2,1) .2s both}}
@keyframes draw{{from{{stroke-dashoffset:var(--len)}}to{{stroke-dashoffset:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def svg(w, h, body, label, css="", weights=(700, 900)):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" xml:space="preserve" role="img" aria-label="{escape(label)}">'
        f"<style>{font_css(body, weights)}{BASE_CSS}{css}</style>{body}</svg>"
    )


def card(w, h, c, rx=16, x=0, y=0):
    return (f'<rect x="{x+.5}" y="{y+.5}" width="{w-1}" height="{h-1}" rx="{rx}" '
            f'fill="{c["surface"]}" stroke="{c["border"]}"/>')


def spans(segs, c):
    """[(texto, color_key), ...] -> tspans en una sola línea."""
    out, pend = [], ""
    for t, k in segs:
        if t.startswith("@") and k == "":
            pend = f' x="{t[1:]}"'; continue
        out.append(f'<tspan{pend} fill="{c[k]}">{escape(t)}</tspan>'); pend = ""
    return "".join(out)


def pill(c, x, y, txt, color="green", fs=11):
    """Etiqueta con fondo teñido y texto del color de acento."""
    w = text_width(txt, fs, 700) + len(txt) * .8 + 20
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="22" rx="11" fill="{c[TINT[color]]}"/>'
            f'<text x="{x + w/2:.1f}" y="{y + 15}" text-anchor="middle" class="disp" font-size="{fs}" '
            f'font-weight="700" letter-spacing=".8" fill="{c[color]}">{escape(txt)}</text>'), w


def tags_row(c, x, y, tags, dot="green"):
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


def window(c, W, H, title):
    """Marco de terminal: barra con tres puntos y título centrado."""
    return (card(W, H, c) + f'<path d="M1 44h{W-2}" stroke="{c["border"]}"/>'
            + "".join(f'<circle cx="{26+i*20}" cy="22" r="6" fill="{c["border"]}"/>' for i in range(3))
            + f'<text x="{W/2}" y="27" text-anchor="middle" class="mono" font-size="12.5" fill="{c["muted"]}">{escape(title)}</text>')


def wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    return lines + [cur]


def save(name, theme, content):
    (OUT / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")


# ─────────────────────────── ENCABEZADOS DE SECCIÓN ───────────────────────────
SECTIONS = [
    ("sobre-mi", "Sobre mí", "quién soy y en qué me enfoco"),
    ("lidero", "Proyectos que lidero", "liderazgo técnico y de producto"),
    ("stack", "Stack", "tecnologías con las que construyo"),
    ("formacion", "Formación", "temas en los que me sigo especializando"),
    ("habilidades", "Habilidades", "fortalezas y lenguajes"),
    ("proyectos", "Proyectos", "repositorios públicos destacados"),
    ("actividad", "Actividad", "contribuciones del último año"),
    ("contacto", "Contacto", "hablemos de tu próximo proyecto"),
]


def heading(t, i, slug, title, sub):
    c = PALETTE[t]; W, H = 900, 60
    num = f"{i+1:02d}"
    tw = text_width(title, 26, 700)
    sx = 64 + tw + 14
    lx = sx + len(sub) * 7.2 + 18
    length = W - 8 - lx
    body = [f'<rect x="1" y="12" width="44" height="36" rx="10" fill="{c["gtint"]}" stroke="{c["green"]}" stroke-opacity=".45"/>',
            f'<text x="23" y="35.5" text-anchor="middle" class="mono" font-size="14" font-weight="700" fill="{c["green"]}">{num}</text>',
            f'<text x="64" y="40" class="disp" font-size="26" font-weight="700" fill="{c["text"]}">{escape(title)}</text>',
            f'<text x="{sx:.1f}" y="39" class="mono" font-size="12.5" fill="{c["muted"]}">{escape(sub)}</text>',
            f'<defs><linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{lx:.1f}" y1="0" x2="{W-8}" y2="0">'
            f'<stop offset="0" stop-color="{c["green"]}"/><stop offset="1" stop-color="{c["orange"]}"/></linearGradient></defs>',
            f'<path class="draw" style="--len:{length:.0f}" d="M{lx:.1f} 34.5H{W-8}" stroke="url(#g)" stroke-width="2" '
            f'stroke-linecap="round" stroke-dasharray="{length:.0f}" stroke-opacity=".8"/>',
            f'<circle cx="{W-5}" cy="34.5" r="3.5" fill="{c["orange"]}"/>']
    save(f"h-{slug}", t, svg(W, H, "".join(body), f"{num} · {title}: {sub}", weights=(700,)))


# ─────────────────────────── WHOAMI ───────────────────────────
def profile_card(c, x, y, w, h):
    """Tarjeta de perfil: monograma, nombre, cifras y disponibilidad."""
    cx = x + w / 2
    b = [f'<defs><linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["green"]}"/>'
         f'<stop offset="1" stop-color="{c["orange"]}"/></linearGradient></defs>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{c["surface2"]}" stroke="{c["border"]}"/>',
         f'<circle cx="{cx}" cy="{y+62}" r="36" fill="{c["surface"]}" stroke="url(#ring)" stroke-width="3"/>',
         f'<text x="{cx}" y="{y+72}" text-anchor="middle" class="disp" font-size="27" font-weight="900" fill="{c["text"]}">MR</text>',
         f'<text x="{cx}" y="{y+124}" text-anchor="middle" class="disp" font-size="18" font-weight="700" fill="{c["text"]}">Maykol Rojas</text>',
         f'<text x="{cx}" y="{y+144}" text-anchor="middle" class="sans" font-size="12.5" fill="{c["muted"]}">Software Engineer</text>',
         # bandera del Perú
         f'<g transform="translate({cx-46} {y+158})"><rect width="7" height="13" fill="#d91023"/>'
         f'<rect x="7" width="7" height="13" fill="#ffffff"/><rect x="14" width="7" height="13" fill="#d91023"/>'
         f'<rect x=".5" y=".5" width="20" height="12" fill="none" stroke="{c["border"]}"/></g>',
         f'<text x="{cx-18}" y="{y+169}" class="sans" font-size="12.5" fill="{c["muted"]}">Lima, Perú</text>',
         f'<path d="M{x+18} {y+192}h{w-36}" stroke="{c["border"]}"/>']
    for i, (num, label, col) in enumerate([("3", "proyectos que lidero", "green"), ("1", "startup co-fundada", "orange")]):
        yy = y + 236 + i * 58
        b.append(f'<text x="{x+20}" y="{yy}" class="disp" font-size="34" font-weight="900" fill="{c[col]}">{num}</text>')
        for j, part in enumerate(wrap(label, 11)):
            b.append(f'<text x="{x+50}" y="{yy-16+j*16}" class="sans" font-size="12.5" fill="{c["muted"]}">{escape(part)}</text>')
    yy = y + 330
    xx = x + 18
    for k, (chip, col) in enumerate([("Mobile", "green"), ("IA", "orange"), ("UX", "green"), ("Scrum", "orange")]):
        p, pw = pill(c, xx, yy + (k // 2) * 30, chip, col)
        b.append(p)
        xx = x + 18 if k % 2 else xx + pw + 8
    yb = y + h - 24
    b.append(f'<circle class="pulse" cx="{x+25}" cy="{yb-4}" r="7" fill="{c["green"]}" opacity=".35"/>'
             f'<circle cx="{x+25}" cy="{yb-4}" r="4" fill="{c["green"]}"/>'
             f'<text x="{x+38}" y="{yb}" class="sans" font-size="13" fill="{c["green"]}">Disponible</text>')
    return f'<g class="in" style="animation-delay:.3s">{"".join(b)}</g>'


def whoami(t):
    c = PALETTE[t]; W = 900
    P = [("kmykh", "green"), (" ~ ", "muted"), ("❯ ", "orange")]
    def kv(k, v, last=False):
        return [("@48", ""), (k, "text"), ("@178", "")] + v + ([] if last else [(",", "muted")])
    s = lambda x: [(f'"{x}"', "green")]
    arr = lambda *xs: [("[", "muted")] + sum([s(x) + ([(", ", "muted")] if i < len(xs) - 1 else []) for i, x in enumerate(xs)], []) + [("]", "muted")]
    lines = [
        P + [("whoami", "text")],
        [],
        [("const ", "orange"), ("maykol", "text"), (" = {", "muted")],
        kv("rol:", s("Software Engineer · Mobile & IA")),
        kv("ahora:", s("IA en aplicaciones móviles")),
        kv("enfoque:", arr("proyectos con IA", "apps móviles", "aplicaciones")),
        kv("lidero:", arr("Aura Nova", "Aliada", "Vitalify")),
        kv("especialidad:", arr("apps móviles", "UX Design", "arquitectura", "Scrum")),
        kv("ia:", s("uso responsable · ética · sesgos · legal")),
        kv("equipo:", s("Co-founder @ MindaCode")),
        kv("base:", s("Lima, Perú")),
        kv("disponible:", [("true", "orange")], last=True),
        [("};", "muted")],
        [],
        P + [("▍", "orange")],
    ]
    y0, step = 92, 29; H = y0 + step * (len(lines) - 1) + 34
    body = [window(c, W, H, "maykol@kmykh — zsh")]
    for i, segs in enumerate(lines):
        if not segs: continue
        cls = ' class="caret"' if segs[-1][0] == "▍" else ""
        inner = (spans(segs[:-1], c) + f'<tspan{cls} fill="{c["orange"]}">▍</tspan>') if cls else spans(segs, c)
        body.append(f'<g class="in" style="animation-delay:{.2+i*.1:.2f}s"><text x="32" y="{y0+i*step}" class="mono" font-size="15">{inner}</text></g>')
    body.append(profile_card(c, 712, 64, 164, H - 84))
    save("whoami", t, svg(W, H, "".join(body), "Terminal: whoami de Maykol Rojas, con tarjeta de perfil"))


# ─────────────────────────── PROYECTOS QUE LIDERO ───────────────────────────
LEADS = [
    ("AN", "Aura Nova", "E-commerce · negocio", ["LÍDER"],
     "Plataforma de e-commerce oficial de Aura Nova, tienda de detalles. Desarrollo y lidero el producto de punta a punta.",
     ["e-commerce", "negocio"], "orange"),
    ("AL", "Aliada", "App móvil · seguridad", ["CO-CREADOR", "LÍDER"],
     "App de seguridad para universitarias: alarma que avisa a personas cercanas con tu ubicación en el mapa, y LumAI, asistente confidencial.",
     ["seguridad", "LumAI"], "green"),
    ("VT", "Vitalify", "Salud digital · IoT", ["LÍDER"],
     "Monitoreo de signos vitales para salud digital. Lidero el desarrollo y al equipo del proyecto.",
     ["salud", "IoT"], "orange"),
]


def leads(t):
    c = PALETTE[t]; W, H = 900, 316; cw, gap = 284, 24
    body = []
    for i, (ini, name, cat, roles, desc, tags, col) in enumerate(LEADS):
        x = i * (cw + gap)
        b = [card(cw, H - 2, c, 16, x, 1),
             f'<rect x="{x+22}" y="24" width="48" height="48" rx="13" fill="{c[TINT[col]]}"/>',
             f'<text x="{x+46}" y="55" text-anchor="middle" class="disp" font-size="19" font-weight="900" fill="{c[col]}">{ini}</text>',
             f'<text x="{x+84}" y="47" class="disp" font-size="23" font-weight="700" fill="{c["text"]}">{escape(name)}</text>',
             f'<text x="{x+84}" y="66" class="mono" font-size="11.5" fill="{c["muted"]}">{escape(cat)}</text>']
        px = x + 22
        for role in roles:
            p, pw = pill(c, px, 90, role, col)
            b.append(p); px += pw + 6
        for j, line in enumerate(wrap(desc, 34)[:5]):
            b.append(f'<text x="{x+22}" y="{144+j*20}" class="sans" font-size="14" fill="{c["muted"]}">{escape(line)}</text>')
        b.append(f'<path d="M{x+22} {H-62}h{cw-44}" stroke="{c["border"]}" stroke-dasharray="3 5"/>')
        b.append(tags_row(c, x + 22, H - 44, tags, col))
        body.append(f'<g class="in" style="animation-delay:{.1+i*.15:.2f}s">{"".join(b)}</g>')
    save("leads", t, svg(W, H, "".join(body), "Proyectos que lidero: Aura Nova, Aliada (con LumAI) y Vitalify"))


# ─────────────────────────── STACK ───────────────────────────
# Solo lenguajes de programación en "lenguajes" (HTML/CSS no lo son).
STACK = [
    ("lenguajes", ["Dart", "TypeScript", "JavaScript", "Java", "C#", "SQL"]),
    ("mobile",    ["Flutter", "Android", "iOS"]),
    ("ia",        ["IA generativa", "prompt engineering", "IA responsable"]),
    ("web",       ["React", "Next.js", "Spring Boot", "ASP.NET Core"]),
    ("datos",     ["PostgreSQL", "Supabase"]),
    ("ux / ui",   ["Figma", "UX Design", "prototipado"]),
    ("método",    ["Scrum", "gestión de equipos", "Git"]),
    ("extra",     ["Docker", "ESP32", "Unity"]),
]


def stack(t):
    c = PALETTE[t]; W = 900; y0, step = 84, 32
    H = y0 + step * len(STACK) + 58
    body = [window(c, W, H, "maykol@kmykh — stack.json")]
    for i, (k, vals) in enumerate(STACK):
        y = y0 + i * step + 8
        col = "green" if i % 2 == 0 else "orange"
        segs = [(k, "text"), ("@178", "")]
        for j, v in enumerate(vals):
            segs.append((v, col if j == 0 else "text"))
            if j < len(vals) - 1: segs.append(("  ·  ", "muted"))
        body.append(f'<g class="in" style="animation-delay:{.15+i*.08:.2f}s">'
                    f'<rect x="34" y="{y-10}" width="10" height="10" rx="3" fill="{c[col]}"/>'
                    f'<text x="58" y="{y}" class="mono" font-size="15">{spans(segs, c)}</text></g>')
    fy = H - 24
    body.append(f'<path d="M24 {fy-26}h{W-48}" stroke="{c["border"]}" stroke-dasharray="3 5"/>')
    body.append(f'<g class="in" style="animation-delay:.9s"><text x="32" y="{fy}" class="mono" font-size="13.5">'
                f'{spans([("status: ", "muted"), ("disponible", "green"), ("   ·   método: ", "muted"), ("Scrum", "text"), ("   ·   ", "muted"), ("open to work", "orange")], c)}</text></g>')
    save("stack", t, svg(W, H, "".join(body), "Stack tecnológico de Maykol Rojas"))


# ─────────────────────────── FORMACIÓN ───────────────────────────
TOPICS = [
    ("IA ética y sesgos en IA", "IA RESPONSABLE", "orange"),
    ("Aspectos legales de la IA", "IA RESPONSABLE", "orange"),
    ("Big Data y ciencia de datos", "DATOS", "green"),
    ("IA generativa y prompt engineering", "IA GENERATIVA", "orange"),
    ("Scrum", "AGILE", "green"),
]


def topics(t):
    c = PALETTE[t]; W = 900; y0, step = 70, 46
    H = y0 + step * len(TOPICS) + 62
    body = [window(c, W, H, "maykol@kmykh — temas.log")]
    for i, (topic, cat, col) in enumerate(TOPICS):
        y = y0 + i * step
        p, pw = pill(c, 0, y + 6, cat, col)
        body.append(f'<g class="in" style="animation-delay:{.15+i*.1:.2f}s">'
                    f'<rect x="24" y="{y}" width="{W-48}" height="34" rx="9" fill="{c["surface2"]}"/>'
                    f'<text x="46" y="{y+22}" text-anchor="middle" class="mono" font-size="13" font-weight="700" fill="{c[col]}">{i+1:02d}</text>'
                    f'<path d="M68 {y+9}v16" stroke="{c["border"]}" stroke-width="1.5"/>'
                    f'<text x="84" y="{y+23}" class="disp" font-size="17.5" font-weight="700" fill="{c["text"]}">{escape(topic)}</text>'
                    f'<g transform="translate({W - 34 - pw:.1f} 0)">{p}</g></g>')
    fy = H - 24
    body.append(f'<path d="M24 {fy-26}h{W-48}" stroke="{c["border"]}" stroke-dasharray="3 5"/>')
    body.append(f'<g class="in" style="animation-delay:.8s"><text x="32" y="{fy}" class="mono" font-size="13.5">'
                f'{spans([("kmykh", "green"), (" ~ ", "muted"), ("❯ ", "orange"), ("tail -f temas.log", "text"), ("   ·   enfoque: ", "muted"), ("IA responsable", "orange")], c)}'
                f'<tspan class="caret" fill="{c["orange"]}"> ▍</tspan></text></g>')
    save("topics", t, svg(W, H, "".join(body), "Formación: " + ", ".join(tp for tp, _, _ in TOPICS)))


# ─────────────────────────── HABILIDADES (radares) ───────────────────────────
# Puntajes 0-100: ajústalos a tu criterio.
RADARS = {
    "radar-skills": ("skills.radar", "habilidades", [
        ("IA generativa", 78), ("Mobile", 88), ("UX Design", 84),
        ("Liderazgo", 85), ("Arquitectura", 78), ("Scrum", 82)]),
    "radar-langs": ("langs.radar", "lenguajes", [
        ("Dart", 70), ("TypeScript", 80), ("JavaScript", 85),
        ("Java", 75), ("C#", 75), ("SQL", 78)]),
}


def radar(t, name):
    c = PALETTE[t]; W, H = 440, 420; cx, cy, R = 220, 232, 112
    title, sub, data = RADARS[name]; n = len(data)
    pt = lambda i, r: (cx + r * math.sin(2 * math.pi * i / n), cy - r * math.cos(2 * math.pi * i / n))
    body = [card(W, H, c),
            f'<text x="24" y="38" class="mono" font-size="13.5">{spans([("$ ", "orange"), ("cat ", "muted"), (title, "text")], c)}</text>',
            f'<text x="{W-24}" y="38" text-anchor="end" class="mono" font-size="12.5" fill="{c["muted"]}">{sub}</text>']
    for f in (.25, .5, .75, 1):
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, R * f) for i in range(n)))
        dash = ' stroke-dasharray="3 4"' if f < 1 else ""
        body.append(f'<polygon points="{poly}" fill="none" stroke="{c["border"]}"{dash}/>')
    for i in range(n):
        x, y = pt(i, R); body.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{c["border"]}"/>')
    rel = [(R * v / 100 * math.sin(2 * math.pi * i / n), -R * v / 100 * math.cos(2 * math.pi * i / n)) for i, (_, v) in enumerate(data)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in rel)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{c["surface"]}" stroke="{c["orange"]}" stroke-width="2.5"/>' for x, y in rel)
    body.append(f'<g transform="translate({cx} {cy})"><g class="grow">'
                f'<polygon points="{poly}" fill="{c["green"]}" fill-opacity=".16" stroke="{c["green"]}" stroke-width="2.5" stroke-linejoin="round"/>{dots}</g></g>')
    for i, (label, v) in enumerate(data):
        x, y = pt(i, R + 22)
        anchor = "middle" if abs(x - cx) < 5 else ("start" if x > cx else "end")
        dy = -18 if y < cy - R * .9 else (12 if y > cy + R * .9 else -2)
        body.append(f'<text x="{x:.1f}" y="{y+dy:.1f}" text-anchor="{anchor}" class="disp" font-size="14" font-weight="700" fill="{c["text"]}">{escape(label)}'
                    f'<tspan x="{x:.1f}" dy="17" class="mono" font-size="12" font-weight="400" fill="{c["muted"]}">{v}</tspan></text>')
    css = """.grow{animation:grow 1.2s cubic-bezier(.2,.8,.2,1) .3s both}
    @keyframes grow{from{transform:scale(0);opacity:0}to{transform:scale(1);opacity:1}}"""
    save(name, t, svg(W, H, "".join(body), f"Radar de {sub}", css, weights=(700,)))


# ─────────────────────────── PROYECTOS PÚBLICOS ───────────────────────────
PROJECTS = [
    ("AppMovil-VacApp", "App móvil personal para la gestión de vacas.", ["Flutter", "Dart"]),
    ("AccesiTour", "Plataforma autónoma para personas con discapacidad en entornos arqueológicos.", ["TypeScript", "accesibilidad"]),
    ("Page-Mindacode", "Web de la startup MindaCode, donde soy co-founder.", ["TypeScript", "web"]),
    ("VideoGame-MaskInThePit", "Videojuego 2D sobre la locura como estrés. Capítulo 1.", ["Unity", "C#"]),
    ("Page-Transportify", "Landing page para una empresa de transporte.", ["web", "landing"]),
    ("Page-Donfy", "Página web del proyecto Donfy.", ["web", "landing"]),
]
# libro (repositorio), 16×16
REPO_ICON = ('<path d="M3 1.5h10v11H4.6A1.6 1.6 0 0 0 3 14.1Z"/>'
             '<path d="M3 14.1a1.6 1.6 0 0 0 1.6 1.4H13v-3"/><path d="M6 4.5h4"/>')


def project(t, i, name, desc, tags):
    c = PALETTE[t]; W, H = 440, 168
    col = "green" if i % 2 == 0 else "orange"
    b = [card(W, H, c, 14),
         f'<g transform="translate(24 27)" fill="none" stroke="{c["muted"]}" stroke-width="1.5" '
         f'stroke-linecap="round" stroke-linejoin="round">{REPO_ICON}</g>',
         f'<text x="50" y="42" class="disp" font-size="19" font-weight="700" fill="{c["text"]}">{escape(name)}</text>',
         f'<text x="{W-24}" y="42" text-anchor="end" class="sans" font-size="18" fill="{c["orange"]}">↗</text>']
    for j, line in enumerate(wrap(desc, 50)[:2]):
        b.append(f'<text x="24" y="{74+j*21}" class="sans" font-size="14" fill="{c["muted"]}">{escape(line)}</text>')
    b.append(tags_row(c, 24, 124, tags, col))
    body = f'<g class="in" style="animation-delay:{.1+i*.08:.2f}s">{"".join(b)}</g>'
    save(f"project-{name.lower()}", t, svg(W, H, body, f"Proyecto {name}"))


# ─────────────────────────── CIERRE ───────────────────────────
def footer(t):
    c = PALETTE[t]; W, H = 900, 116
    body = [f'<defs><linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{W/2-160}" y1="0" x2="{W/2+160}" y2="0">'
            f'<stop offset="0" stop-color="{c["green"]}" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="{c["green"]}"/><stop offset=".5" stop-color="{c["orange"]}"/>'
            f'<stop offset="1" stop-color="{c["orange"]}" stop-opacity="0"/></linearGradient></defs>',
            f'<path d="M{W/2-160} 18H{W/2+160}" stroke="url(#g)" stroke-width="2"/>',
            f'<circle cx="{W/2}" cy="18" r="4" fill="{c["surface"]}" stroke="{c["orange"]}" stroke-width="2"/>',
            f'<text x="{W/2}" y="64" text-anchor="middle" class="disp" font-size="28" font-weight="700" fill="{c["text"]}">Gracias por la visita</text>',
            f'<text x="{W/2}" y="96" text-anchor="middle" class="mono" font-size="13">'
            f'{spans([("status: ", "muted"), ("disponible", "green"), ("  ·  hecho con código y café en Lima, Perú", "muted")], c)}</text>']
    save("footer", t, svg(W, H, "".join(body), "Gracias por la visita", weights=(700,)))


# ─────────────────────────── BUILD ───────────────────────────
if __name__ == "__main__":
    for t in PALETTE:
        for i, sec in enumerate(SECTIONS): heading(t, i, *sec)
        whoami(t); leads(t); stack(t); topics(t); footer(t)  # el banner lo genera scripts/banner/generate.py
        for r in RADARS: radar(t, r)
        for i, p in enumerate(PROJECTS): project(t, i, *p)
    print(f"SVGs generados en {OUT}")
