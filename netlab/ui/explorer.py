"""HeaderExplorer — кликабельная схема заголовка протокола по 32 бита в строке."""
from __future__ import annotations

import tkinter as tk

from .. import theme as T
from ..i18n import _
from .richtext import RichText
from .scene import round_rect
from .widgets import card, label

BW = 21        # пикселей на бит
ROW = 50       # высота строки
MX, MY = 16, 34


class HeaderExplorer(tk.Frame):
    def __init__(self, master, title, fields, note="", bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        self.fields = fields
        label(self, title, 15, "bold").pack(anchor="w")
        if note:
            label(self, note, 10, fg=T.MUTED, wraplength=980, justify="left").pack(anchor="w", pady=(2, 10))
        body = tk.Frame(self, bg=bg)
        body.pack(fill="x")

        layout = self._layout()
        rows = max(piece[0] for pieces in layout for piece in pieces) + 1
        width = MX * 2 + 32 * BW
        height = MY + rows * ROW + 12
        holder = tk.Frame(body, bg=T.BORDER, padx=1, pady=1)
        holder.pack(side="left", anchor="n")
        self.c = tk.Canvas(holder, width=width, height=height, bg=T.CANVAS, highlightthickness=0)
        self.c.pack()

        side = card(body, bg=T.CARD)
        side.pack(side="left", fill="both", expand=True, padx=(14, 0))
        self.info = RichText(side, bg=T.CARD, height=12, padx=18, pady=14, size=11, width=34)
        self.info.pack(fill="both", expand=True)
        self.info.render(_("## Выберите поле\nНажмите на любое поле заголовка слева, чтобы узнать, зачем оно нужно.\n\n"
                           "> Ширина каждой строки — **32 бита** (4 байта). Цифры сверху — номера битов."))
        self._draw(layout)

    def _layout(self):
        pos = 0
        layout = []
        for f in self.fields:
            pieces = []
            left = f.bits
            while left > 0:
                row, col = divmod(pos, 32)
                take = min(left, 32 - col)
                pieces.append((row, col, take))
                pos += take
                left -= take
            layout.append(pieces)
        return layout

    def _draw(self, layout):
        c = self.c
        for b in range(32):
            x = MX + b * BW + BW / 2
            if b % 4 == 0 or b == 31:
                c.create_text(x, 14, text=str(b), fill=T.MUTED, font=T.F(8, mono=True))
            c.create_line(MX + b * BW, 24, MX + b * BW, 28, fill=T.DIM)
        self.items = {}
        for i, (f, pieces) in enumerate(zip(self.fields, layout)):
            color = T.PALETTE[i % len(T.PALETTE)]
            tag = f"field{i}"
            biggest = max(pieces, key=lambda p: p[2])
            for row, col, take in pieces:
                x1 = MX + col * BW + 2
                y1 = MY + row * ROW + 2
                x2 = MX + (col + take) * BW - 2
                y2 = y1 + ROW - 4
                rr = round_rect(c, x1, y1, x2, y2, r=6, fill=T.tint(color, 0.8), outline=T.tint(color, 0.35),
                                width=1.5, tags=(tag, "field"), dash=(4, 3) if f.optional else None)
                self.items.setdefault(i, []).append(rr)
                if (row, col, take) == biggest:
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                    name = f.name if take * BW > len(f.name) * 7 + 6 else f.name.split()[0][: max(3, take * 3)]
                    c.create_text(cx, cy - 7, text=name, fill=T.TEXT, font=T.F(9, "bold"), tags=(tag, "field"))
                    c.create_text(cx, cy + 10, text=_("{n} бит").format(n=f.bits) if not f.optional else _("переменная"),
                                  fill=T.MUTED, font=T.F(8), tags=(tag, "field"))
            c.tag_bind(tag, "<Button-1>", lambda e, i=i: self.select(i))
            c.tag_bind(tag, "<Enter>", lambda e: c.configure(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda e: c.configure(cursor=""))
        self.selected = None

    def select(self, i):
        if self.selected is not None:
            color = T.PALETTE[self.selected % len(T.PALETTE)]
            for it in self.items[self.selected]:
                self.c.itemconfigure(it, fill=T.tint(color, 0.8), outline=T.tint(color, 0.35), width=1.5)
        color = T.PALETTE[i % len(T.PALETTE)]
        for it in self.items[i]:
            self.c.itemconfigure(it, fill=T.tint(color, 0.45), outline=color, width=3)
        self.selected = i
        f = self.fields[i]
        if f.optional:
            size = _("переменный")
        else:
            size = _("{n} бит").format(n=f.bits)
            if f.bits % 8 == 0:
                size += " " + _("({n} байт)").format(n=f.bits // 8)
        text = f"## {f.name}\n" + _("**Размер:** {size}").format(size=size) + f"\n\n{_(f.desc)}"
        if f.example:
            text += "\n\n" + _("**Пример значения:** `{v}`").format(v=_(f.example))
        self.info.render(text)
