#!/usr/bin/env python3
"""
Contribuciones de GitHub animadas: un auto recorre el calendario del último
año semana por semana (en zigzag) y va encendiendo los días con actividad
hasta llegar a "hoy".

La ejecuta .github/workflows/race.yml cada 12 horas y publica race-dark.svg /
race-light.svg en la rama `output`.

Uso local:  python3 scripts/race.py [carpeta_salida]
            token: GITHUB_TOKEN o, si no existe, `gh auth token`
"""
import json
import math
import os
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from build import PALETTE, spans, svg

USER = os.environ.get("GITHUB_USER", "Kmykh")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "dist"

QUERY = """query($login: String!) { user(login: $login) { contributionsCollection { contributionCalendar {
  totalContributions weeks { contributionDays { date contributionCount contributionLevel weekday } } } } } }"""

LEVELS = {  # sin actividad → mucha actividad (verdes de la marca)
    "dark": ["#172019", "#0f4a2a", "#127a3b", "#1fae4f", "#3ddc6f"],
    "light": ["#edf2ee", "#bfe6cb", "#7ccb97", "#34a35c", "#17733c"],
}
LEVEL_INDEX = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
EXTRA = {
    "dark": {"track": "#141a16", "tyre": "#5d6a62", "flash": "#ffb36b"},
    "light": {"track": "#f4f8f5", "tyre": "#2a3530", "flash": "#f59e4c"},
}
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

W, H = 900, 300
P, CELL = 14, 11                   # paso de la grilla y tamaño de cada día
X0, Y0 = 93, 150                   # esquina de la grilla
SPEED, LEAD, HOLD = 280, .8, 4.0   # px/s del auto, espera al inicio y pausa al llegar a hoy


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def stats(days):
    """Racha máxima, racha actual y mejor día (como GitHub: hoy en 0 no corta la racha)."""
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    current, tail = 0, (days[:-1] if days and not days[-1]["contributionCount"] else days)
    for d in reversed(tail):
        if not d["contributionCount"]: break
        current += 1
    best = max(days, key=lambda d: d["contributionCount"])
    return longest, current, best


def seguidos(n):
    return "día seguido" if n == 1 else "días seguidos"


def cx(col): return X0 + col * P + CELL / 2
def cy(row): return Y0 + row * P + CELL / 2


def track(cols):
    """Zigzag por las columnas: baja, gira, sube… y termina en la columna de "hoy"."""
    r = P / 2
    d = [f"M{cx(0):.1f} {cy(0) - P:.1f}"]
    for col in range(cols):
        down = col % 2 == 0
        d.append(f"V{cy(6) if down else cy(0):.1f}")
        d.append(f"A{r} {r} 0 0 {0 if down else 1} {cx(col + 1):.1f} {cy(6) if down else cy(0):.1f}")
    d.append(f"V{cy(3):.1f}")
    length = P + cols * (6 * P + math.pi * r) + 3 * P
    return "".join(d), length


def dist_to(col, row):
    return P + col * (6 * P + math.pi * P / 2) + (row if col % 2 == 0 else 6 - row) * P


def car(c, e):
    """Auto visto desde arriba, apuntando hacia +x (animateMotion lo rota)."""
    return (f'<g filter="url(#glow)" transform="scale(1.3)">'
            f'<rect x="-12.5" y="-6" width="3" height="12" rx="1" fill="{c["orange"]}"/>'
            f'<rect x="-10" y="-7" width="5.5" height="3.2" rx="1" fill="{e["tyre"]}"/>'
            f'<rect x="-10" y="3.8" width="5.5" height="3.2" rx="1" fill="{e["tyre"]}"/>'
            f'<rect x="4" y="-6.5" width="4.5" height="2.8" rx="1" fill="{e["tyre"]}"/>'
            f'<rect x="4" y="3.7" width="4.5" height="2.8" rx="1" fill="{e["tyre"]}"/>'
            f'<path d="M-10-2.4L-5-3.8H1.5L9-1.2L12.5 0L9 1.2L1.5 3.8H-5L-10 2.4Z" fill="{c["orange"]}"/>'
            f'<circle cx="0" cy="0" r="1.5" fill="{e["tyre"]}"/>'
            f'<rect x="10.5" y="-5.5" width="2.5" height="11" rx="1" fill="{c["orange"]}"/></g>')


def render(theme, cal):
    c, e, lv = PALETTE[theme], EXTRA[theme], LEVELS[theme]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    cols = len(weeks)
    longest, current, best = stats(days)
    path, length = track(cols)
    sweep = length / SPEED
    T = LEAD + sweep + HOLD
    k = lambda s: f"{max(0.0, min(1.0, s / T)):.4f}"

    b = [f'<defs><filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
         f'<feDropShadow dx="0" dy="0" stdDeviation="1.4" flood-color="{c["orange"]}" flood-opacity=".5"/></filter></defs>',
         f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="{c["surface"]}" stroke="{c["border"]}"/>',
         f'<text x="28" y="38" class="mono" font-size="14">{spans([("$ ", "orange"), ("git log ", "muted"), ("--since=1.year", "text")], c)}</text>',
         f'<text x="{W-28}" y="38" text-anchor="end" class="mono" font-size="12.5" fill="{c["muted"]}">'
         f'{days[0]["date"][:7]} → {days[-1]["date"][:7]}</text>']

    # cifras del año
    bd = date.fromisoformat(best["date"])
    tiles = [("CONTRIBUCIONES", f'{cal["totalContributions"]}', "último año", "green"),
             ("MEJOR DÍA", f'{best["contributionCount"]}', f"{bd.day} {MESES[bd.month - 1]} {bd.year}", "orange"),
             ("RACHA MÁXIMA", f"{longest}", seguidos(longest), "green"),
             ("RACHA ACTUAL", f"{current}", seguidos(current), "orange")]
    tw = (W - 56 - 3 * 12) / 4
    for i, (label, val, unit, col) in enumerate(tiles):
        x = 28 + i * (tw + 12)
        b.append(f'<g class="in" style="animation-delay:{.1 + i * .1:.1f}s">'
                 f'<rect x="{x:.1f}" y="56" width="{tw:.1f}" height="54" rx="8" fill="{c["surface2"]}" stroke="{c["border"]}"/>'
                 f'<path d="M{x + 1.5:.1f} 64v38" stroke="{c[col]}" stroke-width="3"/>'
                 f'<text x="{x + 16:.1f}" y="75" class="mono" font-size="10" letter-spacing="1.5" fill="{c["muted"]}">{label}</text>'
                 f'<text x="{x + 15:.1f}" y="100" class="disp" font-size="24" font-weight="700" fill="{c["text"]}">{val}'
                 f'<tspan dx="8" class="mono" font-size="11" font-weight="400" fill="{c["muted"]}">{escape(unit)}</tspan></text></g>')

    # meses y días
    last = -9
    for col, w in enumerate(weeks):
        firsts = [date.fromisoformat(d["date"]) for d in w["contributionDays"] if d["date"].endswith("-01")]
        if firsts and col - last >= 3:
            b.append(f'<text x="{X0 + col * P:.1f}" y="{Y0 - 16}" class="mono" font-size="11" fill="{c["muted"]}">{MESES[firsts[0].month - 1]}</text>')
            last = col
    for row, name in [(1, "lun"), (3, "mié"), (5, "vie")]:
        b.append(f'<text x="{X0 - 10}" y="{cy(row) + 4:.1f}" text-anchor="end" class="mono" font-size="10.5" fill="{c["muted"]}">{name}</text>')

    # recorrido, marcador de hoy y días
    b.append(f'<path d="{path}" fill="none" stroke="{e["track"]}" stroke-width="{P + 4}" stroke-linejoin="round"/>')
    hx = X0 + cols * P + CELL / 2
    b.append(f'<path d="M{hx:.1f} {Y0}V{Y0 + 7 * P - 3}" stroke="{c["orange"]}" stroke-width="2" stroke-dasharray="2 4" stroke-linecap="round"/>'
             f'<text x="{hx:.1f}" y="{Y0 - 16}" text-anchor="middle" class="mono" font-size="11" fill="{c["orange"]}">hoy</text>')
    for col, w in enumerate(weeks):
        for d in w["contributionDays"]:
            row, lvl = d["weekday"], LEVEL_INDEX[d["contributionLevel"]]
            x, y = X0 + col * P, Y0 + row * P
            title = f'<title>{d["date"]}: {d["contributionCount"]}</title>'
            if not lvl:
                b.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{lv[0]}"/>')
                continue
            tc = LEAD + dist_to(col, row) / SPEED
            kt = ";".join([k(0), k(tc), k(tc + .15), k(tc + .7), k(T - .4), "1"])
            b.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{lv[lvl]}">{title}'
                     f'<animate attributeName="fill" dur="{T:.2f}s" repeatCount="indefinite" keyTimes="{kt}" '
                     f'values="{lv[0]};{lv[0]};{e["flash"]};{lv[lvl]};{lv[lvl]};{lv[0]}"/></rect>')

    # auto
    end = LEAD + sweep
    b.append(f'<g opacity="0">{car(c, e)}'
             f'<animateMotion dur="{T:.2f}s" repeatCount="indefinite" rotate="auto" calcMode="linear" '
             f'keyPoints="0;0;1;1" keyTimes="0;{k(LEAD)};{k(end)};1" path="{path}"/>'
             f'<animate attributeName="opacity" dur="{T:.2f}s" repeatCount="indefinite" '
             f'keyTimes="0;{k(.25)};{k(T - .5)};{k(T - .25)};1" values="0;1;1;0;0"/></g>')

    # pie
    fy = H - 22
    b.append(f'<text x="28" y="{fy}" class="mono" font-size="11.5" fill="{c["muted"]}">'
             f'actualizado {days[-1]["date"]} · cada columna es una semana</text>')
    lx = W - 28 - 5 * 15 - 36
    b.append(f'<text x="{lx - 8}" y="{fy}" text-anchor="end" class="mono" font-size="11.5" fill="{c["muted"]}">menos</text>')
    for i, col in enumerate(lv):
        b.append(f'<rect x="{lx + i * 15}" y="{fy - 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{col}"/>')
    b.append(f'<text x="{W - 28}" y="{fy}" text-anchor="end" class="mono" font-size="11.5" fill="{c["muted"]}">más</text>')
    return svg(W, H, "".join(b), f"Contribuciones de {USER} en el último año: un auto recorre el calendario y enciende los días con actividad")


def main():
    cal = fetch()
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in PALETTE:
        (OUT / f"race-{theme}.svg").write_text(render(theme, cal), encoding="utf-8")
    print(f"race-*.svg en {OUT} · {cal['totalContributions']} contribuciones")


if __name__ == "__main__":
    main()
