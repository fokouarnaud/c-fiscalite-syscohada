"""Primitives communes des générateurs de schémas (SVG inertes, symboles CEI), une formation par module du paquet.

Chaque formation (compta.py, fisca.py) fournit SLUG, EN (libellés anglais), SECTION_DIAGRAMS, QUESTION_DIAGRAMS
et question_dir(module) ; write_formation() écrit ses schémas en français puis en anglais.
"""
import math  # noqa: F401  (repris par les formations avec les autres primitives)
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent.parent
INK, ACCENT, SOFT, PAPER = "#173f58", "#0d665e", "#7d93a0", "#fcfefe"
FONT = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
LANG = "fr"  # langue des libellés ; write_formation() génère aussi la version anglaise
EN = {}  # libellés anglais de la formation en cours d'écriture (tr)


def tr(text):
    if LANG != "en":
        return text
    text = EN.get(text, text)
    return re.sub(r"(\d),(\d)", r"\1.\2", text)


def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Drawing:
    def __init__(self, width, height, title):
        self.w, self.h, self.title = width, height, title
        self.items, self.zones = [], {}

    # --- éléments de base ---------------------------------------------------------------------------------------------
    def add(self, markup):
        self.items.append(markup)

    def wire(self, *points, color=INK, width=2):
        pts = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in points)
        self.add(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>')

    def dot(self, p):
        self.add(f'<circle cx="{fmt(p[0])}" cy="{fmt(p[1])}" r="3.5" fill="{INK}"/>')

    def text(self, x, y, s, anchor="middle", size=13, color=INK, weight="400", italic=False):
        s = tr(s)
        style = ' font-style="italic"' if italic else ""
        self.add(
            f'<text x="{fmt(x)}" y="{fmt(y)}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}"{style}>{escape(s)}</text>'
        )

    def arrow(self, a, b, label=None, color=ACCENT, offset=(0, -8)):
        """Flèche de courant ou de tension, de a vers b."""
        self.wire(a, b, color=color, width=2)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        p1 = (b[0] - 9 * math.cos(ang - 0.45), b[1] - 9 * math.sin(ang - 0.45))
        p2 = (b[0] - 9 * math.cos(ang + 0.45), b[1] - 9 * math.sin(ang + 0.45))
        self.add(f'<polygon points="{fmt(b[0])},{fmt(b[1])} {fmt(p1[0])},{fmt(p1[1])} {fmt(p2[0])},{fmt(p2[1])}" fill="{color}"/>')
        if label:
            mid = ((a[0] + b[0]) / 2 + offset[0], (a[1] + b[1]) / 2 + offset[1])
            self.text(mid[0], mid[1], label, color=color, weight="600")

    def zone(self, name, x, y, w, h):
        self.zones[name] = {"x": round(x), "y": round(y), "w": round(w), "h": round(h)}

    # --- dipôles : dessinés horizontalement puis tournés entre a et b ---------------------------------------------------
    def _two(self, a, b, body, body_len):
        length = math.dist(a, b)
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        lead = (length - body_len) / 2
        self.add(
            f'<g transform="translate({fmt(a[0])},{fmt(a[1])}) rotate({fmt(ang)})" fill="none" stroke="{INK}" stroke-width="2">'
            f'<line x1="0" y1="0" x2="{fmt(lead)}" y2="0"/>'
            f'<line x1="{fmt(lead + body_len)}" y1="0" x2="{fmt(length)}" y2="0"/>'
            f'<g transform="translate({fmt(lead)},0)">{body}</g></g>'
        )
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

    def _label(self, mid, a, b, label, value, side=1):
        if not (label or value):
            return
        vertical = abs(a[0] - b[0]) < 1
        if vertical:
            x = mid[0] + 18 * side
            anchor = "start" if side > 0 else "end"
            if label:
                self.text(x, mid[1] - 2, label, anchor=anchor, weight="600")
            if value:
                self.text(x, mid[1] + 14, value, anchor=anchor, color=SOFT, size=12)
        else:
            y = mid[1] - 16 * side if side > 0 else mid[1] + 26
            if label:
                self.text(mid[0], y - (12 if value and side > 0 else 0), label, weight="600")
            if value:
                self.text(mid[0], y + (0 if side > 0 else 14), value, color=SOFT, size=12)

    def resistor(self, a, b, label=None, value=None, side=1):
        mid = self._two(a, b, '<rect x="0" y="-7" width="36" height="14" rx="2" fill="#fcfefe"/>', 36)
        self._label(mid, a, b, label, value, side)
        return mid

    def ldr(self, a, b, label="LDR", value=None, side=1):
        body = ('<rect x="0" y="-7" width="36" height="14" rx="2" fill="#fcfefe"/><circle cx="18" cy="0" r="16"/>')
        mid = self._two(a, b, body, 36)
        vertical = abs(a[0] - b[0]) < 1
        sx = -1 if vertical else 1
        for k in (-8, 6):
            start = (mid[0] - 36 * sx + (k if not vertical else -6), mid[1] - 30 + (0 if not vertical else k + 30))
            end = (mid[0] - 14 * sx + (k if not vertical else -18), mid[1] - 12 + (0 if not vertical else k + 18))
            if vertical:
                start, end = (mid[0] - 40, mid[1] + k - 14), (mid[0] - 20, mid[1] + k - 4)
            self.arrow(start, end, color=ACCENT)
        self._label(mid, a, b, label, value, side)
        return mid

    def capacitor(self, a, b, label=None, value=None, side=1):
        body = '<line x1="0" y1="0" x2="12" y2="0"/><line x1="12" y1="-13" x2="12" y2="13"/><line x1="20" y1="-13" x2="20" y2="13"/><line x1="20" y1="0" x2="32" y2="0"/>'
        mid = self._two(a, b, body, 32)
        self._label(mid, a, b, label, value, side)
        return mid

    def battery(self, a, b, label=None, value=None, side=-1):
        """Générateur continu : de a (borne −) vers b (borne +)."""
        body = ('<line x1="0" y1="0" x2="12" y2="0"/><line x1="12" y1="-7" x2="12" y2="7" stroke-width="4"/>'
                '<line x1="20" y1="-15" x2="20" y2="15"/><line x1="20" y1="0" x2="32" y2="0"/>')
        mid = self._two(a, b, body, 32)
        vertical = abs(a[0] - b[0]) < 1
        plus = (mid[0] + 12, mid[1] + (-10 if b[1] < a[1] else 16)) if vertical else (mid[0] + 10, mid[1] - 18)
        self.text(plus[0], plus[1], "+", color=ACCENT, weight="700")
        self._label(mid, a, b, label, value, side)
        return mid

    def ac_source(self, a, b, label=None, value=None, side=-1):
        body = '<circle cx="16" cy="0" r="16" fill="#fcfefe"/><path d="M6 0 C 9 -9, 13 -9, 16 0 S 23 9, 26 0"/>'
        mid = self._two(a, b, body, 32)
        self._label(mid, a, b, label, value, side)
        return mid

    def diode(self, a, b, label=None, value=None, side=1, kind="diode"):
        """Diode passante de a (anode) vers b (cathode)."""
        bar = '<line x1="22" y1="-11" x2="22" y2="11"/>'
        if kind == "zener":
            bar = '<polyline points="18,-14 22,-11 22,11 26,14"/>'
        body = f'<polygon points="0,-11 0,11 22,0" fill="#fcfefe"/>{bar}'
        if kind == "led":
            body += ('<line x1="8" y1="-16" x2="18" y2="-27"/><polyline points="12,-27 18,-27 18,-21"/>'
                     '<line x1="16" y1="-14" x2="26" y2="-25"/><polyline points="20,-25 26,-25 26,-19"/>')
        mid = self._two(a, b, body, 22)
        self._label(mid, a, b, label, value, side)
        return mid

    def switch(self, a, b, label=None, closed=False, side=1):
        tip = "34,0" if closed else "32,-14"
        body = f'<circle cx="2" cy="0" r="2.5" fill="{INK}"/><circle cx="34" cy="0" r="2.5" fill="{INK}"/><line x1="2" y1="0" x2="{tip.split(",")[0]}" y2="{tip.split(",")[1]}"/>'
        mid = self._two(a, b, body, 36)
        self._label(mid, a, b, label, None, side)
        return mid

    def lamp(self, a, b, label=None, value=None, side=1, lit=False):
        fill = "#fff0c2" if lit else "#fcfefe"
        body = f'<circle cx="14" cy="0" r="14" fill="{fill}"/><line x1="4" y1="-10" x2="24" y2="10"/><line x1="4" y1="10" x2="24" y2="-10"/>'
        mid = self._two(a, b, body, 28)
        self._label(mid, a, b, label, value, side)
        return mid

    def coil(self, a, b, label="K", value=None, side=1):
        body = '<rect x="0" y="-9" width="30" height="18" fill="#fcfefe"/><line x1="0" y1="9" x2="30" y2="-9"/>'
        mid = self._two(a, b, body, 30)
        self._label(mid, a, b, label, value, side)
        return mid

    def inductor(self, a, b, label=None, value=None, side=1):
        """Bobine (symbole CEI : quatre demi-cercles)."""
        body = '<path d="M0 0 a5 5 0 0 1 10 0 a5 5 0 0 1 10 0 a5 5 0 0 1 10 0 a5 5 0 0 1 10 0"/>'
        mid = self._two(a, b, body, 40)
        self._label(mid, a, b, label, value, side)
        return mid

    def variable_capacitor(self, a, b, label=None, value=None, side=1):
        body = ('<line x1="0" y1="0" x2="12" y2="0"/><line x1="12" y1="-13" x2="12" y2="13"/><line x1="20" y1="-13" x2="20" y2="13"/>'
                '<line x1="20" y1="0" x2="32" y2="0"/><line x1="2" y1="16" x2="30" y2="-16"/><polyline points="22,-16 30,-16 30,-8"/>')
        mid = self._two(a, b, body, 32)
        self._label(mid, a, b, label, value, side)
        return mid

    def antenna(self, p):
        x, y = p
        self.wire((x, y), (x, y - 40))
        self.wire((x - 14, y - 58), (x, y - 40), (x + 14, y - 58))
        self.wire((x - 14, y - 58), (x + 14, y - 58))

    def meter(self, a, b, letter):
        """Ampèremètre (A) ou voltmètre (V) entre a et b ; la lettre ne tourne pas."""
        mid = self._two(a, b, '<circle cx="15" cy="0" r="15" fill="#fcfefe"/>', 30)
        self.text(mid[0], mid[1] + 5, letter, weight="700")
        return mid

    def ground(self, p):
        x, y = p
        self.wire((x, y), (x, y + 8))
        for i, half in enumerate((12, 8, 4)):
            self.wire((x - half, y + 8 + 5 * i), (x + half, y + 8 + 5 * i))

    # --- composants à trois broches -------------------------------------------------------------------------------------
    def bjt(self, cx, cy, kind="npn", labels=True, circle=True):
        """Transistor bipolaire ; renvoie les extrémités des broches B, C, E."""
        if circle:
            self.add(f'<circle cx="{fmt(cx + 2)}" cy="{fmt(cy)}" r="24" fill="#fcfefe" stroke="{INK}" stroke-width="2"/>')
        self.wire((cx - 40, cy), (cx - 10, cy))
        self.wire((cx - 10, cy - 15), (cx - 10, cy + 15), width=4)
        self.wire((cx - 10, cy - 7), (cx + 12, cy - 22), (cx + 12, cy - 42))
        self.wire((cx - 10, cy + 7), (cx + 12, cy + 22), (cx + 12, cy + 42))
        if kind == "npn":
            tip, back = (cx + 10, cy + 21), (cx - 1, cy + 14)
        else:
            tip, back = (cx - 7, cy + 9), (cx + 4, cy + 16)
        ang = math.atan2(tip[1] - back[1], tip[0] - back[0])
        p1 = (tip[0] - 10 * math.cos(ang - 0.5), tip[1] - 10 * math.sin(ang - 0.5))
        p2 = (tip[0] - 10 * math.cos(ang + 0.5), tip[1] - 10 * math.sin(ang + 0.5))
        self.add(f'<polygon points="{fmt(tip[0])},{fmt(tip[1])} {fmt(p1[0])},{fmt(p1[1])} {fmt(p2[0])},{fmt(p2[1])}" fill="{INK}"/>')
        b, c, e = (cx - 40, cy), (cx + 12, cy - 42), (cx + 12, cy + 42)
        if labels:
            self.text(cx - 34, cy - 8, "B", weight="700", color=ACCENT)
            self.text(cx + 24, cy - 30, "C", weight="700", color=ACCENT)
            self.text(cx + 24, cy + 38, "E", weight="700", color=ACCENT)
        return b, c, e

    def jfet(self, cx, cy, labels=True):
        """JFET canal N ; renvoie G, D, S."""
        self.add(f'<circle cx="{fmt(cx + 4)}" cy="{fmt(cy)}" r="24" fill="#fcfefe" stroke="{INK}" stroke-width="2"/>')
        self.wire((cx - 6, cy - 16), (cx - 6, cy + 16), width=4)
        self.wire((cx - 6, cy - 10), (cx + 14, cy - 10), (cx + 14, cy - 42))
        self.wire((cx - 6, cy + 10), (cx + 14, cy + 10), (cx + 14, cy + 42))
        self.wire((cx - 40, cy + 10), (cx - 6, cy + 10))
        self.add(f'<polygon points="{fmt(cx - 7)},{fmt(cy + 10)} {fmt(cx - 17)},{fmt(cy + 5)} {fmt(cx - 17)},{fmt(cy + 15)}" fill="{INK}"/>')
        g, d, s = (cx - 40, cy + 10), (cx + 14, cy - 42), (cx + 14, cy + 42)
        if labels:
            self.text(cx - 32, cy + 2, "G", weight="700", color=ACCENT)
            self.text(cx + 26, cy - 30, "D", weight="700", color=ACCENT)
            self.text(cx + 26, cy + 38, "S", weight="700", color=ACCENT)
        return g, d, s

    # --- courbes --------------------------------------------------------------------------------------------------------
    def graph(self, x, y, w, h, xr, yr, series, xlabel, ylabel, marks=(), xticks=(), yticks=()):
        """Repère et courbes : series = [(points en unités, couleur, légende)]."""
        def px(v):
            return x + (v - xr[0]) / (xr[1] - xr[0]) * w

        def py(v):
            return y + h - (v - yr[0]) / (yr[1] - yr[0]) * h

        x0, y0 = px(max(xr[0], 0)) if xr[0] < 0 else x, py(max(yr[0], 0)) if yr[0] < 0 else y + h
        self.arrow((x - 4, y0), (x + w + 14, y0), color=INK)
        self.arrow((x0, y + h + 4), (x0, y - 14), color=INK)
        self.text(x + w + 14, y0 - 10, xlabel, anchor="end", size=12)
        self.text(x0 + 8, y - 4, ylabel, anchor="start", size=12)
        for v, s in xticks:
            self.wire((px(v), y0 - 3), (px(v), y0 + 3))
            self.text(px(v), y0 + 16, s, size=11, color=SOFT)
        for v, s in yticks:
            self.wire((x0 - 3, py(v)), (x0 + 3, py(v)))
            self.text(x0 - 6, py(v) + 4, s, anchor="end", size=11, color=SOFT)
        for points, color, legend, *where in series:
            self.wire(*[(px(a), py(b)) for a, b in points], color=color, width=2.5)
            if legend and where:
                self.text(px(where[0][0]), py(where[0][1]), legend, anchor="start", size=12, color=color, weight="600")
            elif legend:
                lx, ly = points[-1]
                self.text(px(lx) - 4, py(ly) - 8, legend, anchor="end", size=12, color=color, weight="600")
        for (a, b), s in marks:
            self.add(f'<line x1="{fmt(px(a))}" y1="{fmt(py(b))}" x2="{fmt(px(a))}" y2="{fmt(y0)}" stroke="{SOFT}" stroke-dasharray="4 3"/>')
            self.text(px(a) + 6, py(b) - 6, s, anchor="start", size=12, color=ACCENT, weight="600")
        return px, py

    def svg(self):
        body = "".join(self.items)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" '
            f'font-family="{FONT}">'
            + (f"<title>{escape(self.title)}</title>" if LANG == "fr" else "")  # en anglais, le texte alternatif de la page suffit
            + f'<rect width="{self.w}" height="{self.h}" rx="14" fill="{PAPER}"/>{body}</svg>\n'
        )


# --- Aides de dessin partagées par les formations -------------------------------------------------------------------


def block(d, x, y, w, h, label, size=12):
    d.add(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" rx="8" fill="#eef4f3" stroke="{INK}" stroke-width="2"/>')
    d.text(x + w / 2, y + h / 2 + 4, label, size=size, weight="600")


def transformer(d, cx, top, n_p=1, n_s=1, dots=None, core=True):
    """Transformateur vertical : enroulements de n segments (4 spires dessinées chacun) ; renvoie p1, p2, s1, s2."""
    xp, xs = cx - 20, cx + 20
    p_bottom, s_bottom = top + 40 * n_p, top + 40 * n_s
    for k in range(n_p):
        d.inductor((xp, top + 40 * k), (xp, top + 40 * (k + 1)))
    for k in range(n_s):
        d.inductor((xs, top + 40 * (k + 1)), (xs, top + 40 * k))
    if core:
        bottom = max(p_bottom, s_bottom)
        d.wire((cx - 4, top - 4), (cx - 4, bottom + 4)); d.wire((cx + 4, top - 4), (cx + 4, bottom + 4))
    if dots:
        d.add(f'<circle cx="{fmt(xp - 12)}" cy="{fmt(top + 6)}" r="3.5" fill="{ACCENT}"/>')
        sy = top + 6 if dots == "same" else s_bottom - 6
        d.add(f'<circle cx="{fmt(xs + 12)}" cy="{fmt(sy)}" r="3.5" fill="{ACCENT}"/>')
    return (xp, top), (xp, p_bottom), (xs, top), (xs, s_bottom)


def terminal(d, p, label=None, anchor="start"):
    d.add(f'<circle cx="{fmt(p[0])}" cy="{fmt(p[1])}" r="4" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>')
    if label:
        d.text(p[0] + (10 if anchor == "start" else -10), p[1] + 5, label, anchor=anchor, weight="600", color=ACCENT)


def rail(d, x1, x2, y, label):
    d.wire((x1, y), (x2, y))
    d.text(x1 - 8, y + 5, label, anchor="end", weight="600")


def file_name(func):
    return func.__name__.split("_", 1)[1].replace("_", "-") + ".svg"


def write_formation(formation, root=ROOT):
    """Sections dans static/content/<slug>/[en/]m<N>/, questions sur schéma dans le dossier de leur partie."""
    global LANG, EN
    EN = formation.EN
    try:
        for LANG, folder in (("fr", ""), ("en", "en")):
            for module, funcs in formation.SECTION_DIAGRAMS.items():
                out = root / "static" / "content" / formation.SLUG / folder / f"m{module}"
                out.mkdir(parents=True, exist_ok=True)
                for func in funcs:
                    (out / file_name(func)).write_text(func().svg(), encoding="utf-8", newline="\n")
        LANG = "fr"
        for module, func in formation.QUESTION_DIAGRAMS.items():
            out = root / formation.question_dir(module).relative_to(ROOT)
            out.mkdir(parents=True, exist_ok=True)
            drawing = func()
            (out / file_name(func)).write_text(drawing.svg(), encoding="utf-8", newline="\n")
            print(f"m{module}/schemas/{file_name(func)} zones : {drawing.zones}")
    finally:
        LANG, EN = "fr", {}
