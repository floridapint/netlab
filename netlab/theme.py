"""Цвета, шрифты и стили ttk (тёмная тема)."""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from .i18n import N_, _

BG = "#0b1220"
SIDEBAR = "#0d1525"
PANEL = "#111b2d"
PANEL2 = "#1a2740"
CARD = "#131f33"
BORDER = "#24324a"
CANVAS = "#0e1829"
CODE_BG = "#0a1322"

TEXT = "#e5edf7"
MUTED = "#93a4bd"
DIM = "#5d6e88"
ON_ACCENT = "#06121f"

ACCENT = "#38bdf8"
ACCENT2 = "#a78bfa"
GOOD = "#4ade80"
BAD = "#f87171"
WARN = "#fbbf24"
PINK = "#f472b6"
ORANGE = "#fb923c"
TEAL = "#2dd4bf"

LAYER = {7: "#f472b6", 6: "#c084fc", 5: "#818cf8", 4: "#38bdf8", 3: "#34d399", 2: "#fbbf24", 1: "#fb923c"}
LAYER_NAMES = {7: N_("Прикладной"), 6: N_("Представления"), 5: N_("Сеансовый"), 4: N_("Транспортный"),
               3: N_("Сетевой"), 2: N_("Канальный"), 1: N_("Физический")}


def layer_name(layer: int) -> str:
    return _(LAYER_NAMES[layer])
PALETTE = ["#38bdf8", "#34d399", "#fbbf24", "#f472b6", "#a78bfa", "#fb923c", "#2dd4bf", "#f87171"]

_family = "Segoe UI"
_mono = "Consolas"
_fonts: dict = {}


def F(size: int = 10, weight: str = "normal", mono: bool = False, italic: bool = False):
    style = weight + (" italic" if italic else "")
    return (_mono if mono else _family, size, style)


def font_obj(spec) -> tkfont.Font:
    key = tuple(spec)
    if key not in _fonts:
        fam, size, style = spec
        _fonts[key] = tkfont.Font(family=fam, size=size, weight="bold" if "bold" in style else "normal",
                                  slant="italic" if "italic" in style else "roman")
    return _fonts[key]


def measure(text: str, spec) -> int:
    return font_obj(spec).measure(text)


def _rgb(c: str):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def mix(a: str, b: str, t: float) -> str:
    """Линейная смесь цветов: t=0 → a, t=1 → b."""
    t = max(0.0, min(1.0, t))
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    return "#%02x%02x%02x" % (round(ra + (rb - ra) * t), round(ga + (gb - ga) * t), round(ba + (bb - ba) * t))


def tint(color: str, amount: float = 0.8, base: str = CANVAS) -> str:
    return mix(color, base, amount)


def init(root: tk.Tk):
    global _family, _mono
    _fonts.clear()  # объекты Font привязаны к конкретному окну Tk
    fams = {f.lower(): f for f in tkfont.families(root)}
    for cand in ("Segoe UI", "Inter", "Ubuntu", "Noto Sans", "Cantarell", "DejaVu Sans", "Helvetica Neue", "Arial"):
        if cand.lower() in fams:
            _family = fams[cand.lower()]
            break
    for cand in ("Cascadia Mono", "Consolas", "JetBrains Mono", "Ubuntu Mono", "DejaVu Sans Mono", "Menlo", "Courier New"):
        if cand.lower() in fams:
            _mono = fams[cand.lower()]
            break

    root.configure(bg=BG)
    root.option_add("*Font", F(10))
    root.option_add("*Background", BG)
    root.option_add("*Foreground", TEXT)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BG, foreground=TEXT, fieldbackground=PANEL2, bordercolor=BORDER,
                    lightcolor=PANEL2, darkcolor=PANEL2, troughcolor=PANEL, focuscolor=ACCENT, font=F(10))
    style.configure("TNotebook", background=BG, borderwidth=1, tabmargins=(0, 0, 0, 0), bordercolor=BORDER,
                    lightcolor=BG, darkcolor=BG)
    style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(18, 8), borderwidth=1,
                    font=F(10, "bold"), bordercolor=BG, lightcolor=PANEL, darkcolor=PANEL)
    style.map("TNotebook.Tab", background=[("selected", PANEL2), ("active", CARD)],
              foreground=[("selected", TEXT), ("active", TEXT)],
              lightcolor=[("selected", ACCENT)], darkcolor=[("selected", PANEL2)],
              expand=[("selected", (0, 0, 0, 0))])
    style.layout("TNotebook.Tab", [("Notebook.tab", {"sticky": "nswe", "children": [
        ("Notebook.padding", {"side": "top", "sticky": "nswe", "children": [
            ("Notebook.label", {"side": "top", "sticky": ""})]})]})])

    for orient in ("Vertical", "Horizontal"):
        style.configure(f"{orient}.TScrollbar", background=PANEL2, troughcolor=BG, bordercolor=BG,
                        arrowcolor=MUTED, lightcolor=PANEL2, darkcolor=PANEL2, gripcount=0, arrowsize=12)
        style.map(f"{orient}.TScrollbar", background=[("active", BORDER), ("pressed", BORDER)])

    for name, color in (("", ACCENT), ("Good.", GOOD), ("Warn.", WARN), ("Bad.", BAD)):
        style.configure(f"{name}Horizontal.TProgressbar", troughcolor=PANEL2, background=color,
                        bordercolor=PANEL2, lightcolor=color, darkcolor=color, thickness=6)

    style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT, rowheight=28,
                    bordercolor=BORDER, borderwidth=0, font=F(10))
    style.configure("Treeview.Heading", background=PANEL2, foreground=TEXT, font=F(10, "bold"),
                    relief="flat", borderwidth=0, padding=(8, 6))
    style.map("Treeview", background=[("selected", "#1e3a5f")], foreground=[("selected", TEXT)])
    style.map("Treeview.Heading", background=[("active", BORDER)])

    style.configure("Horizontal.TScale", background=ACCENT, troughcolor=PANEL2, bordercolor=BG,
                    lightcolor=ACCENT, darkcolor=ACCENT, sliderthickness=16)
