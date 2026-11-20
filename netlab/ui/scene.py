"""Строительные блоки для анимационных сцен: спрайты, пакеты, диаграммы последовательности."""
from __future__ import annotations

import math
import tkinter as tk

from .. import theme as T
from ..i18n import _
from .animation import H, W, Scenario, Step, Tween, ease_in_out, later, linear


def round_rect(c: tk.Canvas, x1, y1, x2, y2, r=8, **kw):
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def grow_line(c, item, x0, y0, x1, y1):
    def fn(t):
        c.coords(item, x0, y0, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
    return fn


def recolor(c, item, attr, a, b):
    def fn(t):
        try:
            c.itemconfigure(item, **{attr: T.mix(a, b, t)})
        except tk.TclError:
            pass
    return fn


def fade_in(c, items, dur=500, delay=0):
    """items: [(item, attr, target_color)] — плавное появление из цвета фона."""
    tws = []
    for item, attr, color in items:
        c.itemconfigure(item, **{attr: T.CANVAS})
        tws.append(Tween(dur, recolor(c, item, attr, T.CANVAS, color), linear, delay))
    return tws


class Sprite:
    _counter = 0

    def __init__(self, c: tk.Canvas, x, y):
        Sprite._counter += 1
        self.tag = f"spr{Sprite._counter}"
        self.c = c
        self.x, self.y = x, y

    def draw(self):
        pass

    def redraw(self):
        self.c.delete(self.tag)
        self.draw()

    def set_pos(self, x, y):
        self.c.move(self.tag, x - self.x, y - self.y)
        self.x, self.y = x, y

    def tween_to(self, x, y, dur=700, delay=0, ease=ease_in_out):
        start = []

        def fn(t):
            if not start:
                start.append((self.x, self.y))
            sx, sy = start[0]
            self.set_pos(sx + (x - sx) * t, sy + (y - sy) * t)
        return Tween(dur, fn, ease, delay)

    def tween_path(self, points, dur=1500, delay=0, ease=ease_in_out):
        """Движение по ломаной [(x, y), ...] с постоянной скоростью."""
        state = {}

        def fn(t):
            if "segs" not in state:
                pts = [(self.x, self.y)] + list(points)
                segs, total = [], 0.0
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    d = math.hypot(bx - ax, by - ay)
                    segs.append((ax, ay, bx, by, total, d))
                    total += d
                state["segs"], state["total"] = segs, total or 1.0
            dist = t * state["total"]
            for ax, ay, bx, by, s0, d in state["segs"]:
                if dist <= s0 + d or (ax, ay, bx, by, s0, d) == state["segs"][-1]:
                    k = 0 if d == 0 else min(1.0, max(0.0, (dist - s0) / d))
                    self.set_pos(ax + (bx - ax) * k, ay + (by - ay) * k)
                    break
        return Tween(dur, fn, ease, delay)

    def delete(self):
        self.c.delete(self.tag)

    def lift(self):
        self.c.tag_raise(self.tag)


class Chip(Sprite):
    """Скруглённая плашка с текстом (сообщение, пакет, датаграмма)."""

    def __init__(self, c, x, y, text, color=T.ACCENT, fg=T.ON_ACCENT, size=9, h=24, pad=10, filled=True):
        super().__init__(c, x, y)
        self.text, self.color, self.fg, self.size, self.h, self.pad, self.filled = text, color, fg, size, h, pad, filled
        self.draw()

    def draw(self):
        f = T.F(self.size, "bold")
        lines = self.text.split("\n")
        w = max(T.measure(line, f) for line in lines) + 2 * self.pad
        h = self.h + (len(lines) - 1) * (self.size + 6)
        fill = self.color if self.filled else T.tint(self.color, 0.8)
        round_rect(self.c, self.x - w / 2, self.y - h / 2, self.x + w / 2, self.y + h / 2, r=8,
                   fill=fill, outline=self.color, width=1.5, tags=(self.tag,))
        self.c.create_text(self.x, self.y, text=self.text, fill=self.fg if self.filled else T.TEXT, font=f,
                           tags=(self.tag,), justify="center")

    def set(self, text=None, color=None, fg=None):
        if text is not None:
            self.text = text
        if color is not None:
            self.color = color
        if fg is not None:
            self.fg = fg
        self.redraw()


class Packet(Sprite):
    """PDU из цветных сегментов: [(подпись, цвет, ширина), ...] + подпись снизу."""

    def __init__(self, c, x, y, segments, caption="", h=30):
        super().__init__(c, x, y)
        self.segments = list(segments)
        self.caption = caption
        self.h = h
        self.draw()

    def draw(self):
        total = sum(s[2] for s in self.segments)
        x = self.x - total / 2
        y1, y2 = self.y - self.h / 2, self.y + self.h / 2
        for text, color, w in self.segments:
            self.c.create_rectangle(x, y1, x + w, y2, fill=color, outline=T.CANVAS, width=2, tags=(self.tag,))
            self.c.create_text(x + w / 2, self.y, text=text, fill=T.ON_ACCENT, font=T.F(8, "bold"), tags=(self.tag,))
            x += w
        if self.caption:
            self.c.create_text(self.x, y2 + 10, text=self.caption, fill=T.MUTED, font=T.F(9, "bold"), tags=(self.tag,))

    def set(self, segments=None, caption=None):
        if segments is not None:
            self.segments = list(segments)
        if caption is not None:
            self.caption = caption
        self.redraw()

    def pulse(self, dur=600, delay=0):
        """Короткая вспышка-обводка вокруг пакета (рисуется в момент начала твина)."""
        ring = []

        def fn(t):
            if not ring:
                total = sum(s[2] for s in self.segments)
                ring.append(self.c.create_rectangle(
                    self.x - total / 2 - 3, self.y - self.h / 2 - 3, self.x + total / 2 + 3, self.y + self.h / 2 + 3,
                    outline="#ffffff", width=3, tags=(self.tag,)))
            try:
                self.c.itemconfigure(ring[0], outline=T.mix("#ffffff", T.CANVAS, t), width=max(1, 3 - 2 * t))
                if t >= 1:
                    self.c.delete(ring[0])
            except tk.TclError:
                pass
        return Tween(dur, fn, linear, delay)


def node_box(c, x, y, w, h, title, subtitle="", color=T.ACCENT, tag=None, size=11):
    """Прямоугольник-устройство с подписью (title/subtitle переводятся). Возвращает id рамки."""
    title, subtitle = _(title), _(subtitle)
    tags = (tag,) if tag else ()
    rect = round_rect(c, x - w / 2, y - h / 2, x + w / 2, y + h / 2, r=10, fill=T.tint(color, 0.82),
                      outline=color, width=2, tags=tags)
    if subtitle:
        c.create_text(x, y - 9, text=title, fill=T.TEXT, font=T.F(size, "bold"), tags=tags)
        c.create_text(x, y + 11, text=subtitle, fill=T.MUTED, font=T.F(8), tags=tags)
    else:
        c.create_text(x, y, text=title, fill=T.TEXT, font=T.F(size, "bold"), tags=tags)
    return rect


def highlight(c, rect, color, on=True):
    c.itemconfigure(rect, fill=T.tint(color, 0.55 if on else 0.82), width=3 if on else 2)


def check_mark(c, x, y, ok=True, size=14):
    return c.create_text(x, y, text="✔" if ok else "✘", fill=T.GOOD if ok else T.BAD, font=T.F(size, "bold"))


# ====================================================================== диаграммы последовательности

class SequenceScenario(Scenario):
    """Классическая диаграмма «клиент ↔ сервер» с наклонными стрелками во времени."""

    actors = [("Client", "192.168.1.10", T.ACCENT), ("Server", "93.184.216.34", T.GOOD)]
    top = 14
    start_y = 96
    dy = 28
    gap = 14
    initial_states = {}

    def actor_xs(self):
        n = len(self.actors)
        if n == 2:
            return [260, 620]
        if n == 3:
            return [150, 440, 730]
        margin = 120
        step = (W - 2 * margin) / (n - 1)
        return [margin + i * step for i in range(n)]

    def build(self, c):
        self.c = c
        self.xs = self.actor_xs()
        self.y = self.start_y
        self.rtt_y = self.start_y
        self.rtt_n = 0
        for (name, sub, color), x in zip(self.actors, self.xs):
            round_rect(c, x - 82, self.top, x + 82, self.top + 50, r=10, fill=T.tint(color, 0.82), outline=color, width=2)
            c.create_text(x, self.top + 17, text=_(name), fill=T.TEXT, font=T.F(11, "bold"))
            c.create_text(x, self.top + 36, text=_(sub), fill=T.MUTED, font=T.F(8, mono=True))
            c.create_line(x, self.top + 50, x, H - 8, fill=T.BORDER, dash=(4, 4), width=2)
        for idx, st in self.initial_states.items():
            self._state(idx, self.start_y - 18, st)
        self.build_extra(c)

    def build_extra(self, c):
        pass

    def _side(self, idx):
        x = self.xs[idx]
        if idx == 0:
            return x - 12, "e"
        return x + 12, "w"

    def _state(self, idx, y, text, color=T.WARN):
        x, anchor = self._side(idx)
        self.c.create_text(x, y, text=text, fill=color, font=T.F(9, "bold", mono=True), anchor=anchor)

    def msg(self, a, b, label, text, title="", color=T.ACCENT, states=None, lost=False, dur=1000, dy=None,
            rtt=False, chip=None):
        """Шаг: сообщение от актёра a к актёру b."""

        def action():
            c = self.c
            x0, x1 = self.xs[a], self.xs[b]
            y0 = self.y
            y1 = y0 + (self.dy if dy is None else dy)
            self.y = y1 + self.gap
            k = 0.55 if lost else 1.0
            xe, ye = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
            line = c.create_line(x0, y0, x0, y0, fill=color, width=2, arrow="none" if lost else "last",
                                 arrowshape=(10, 12, 4))
            sprite = Chip(c, x0, y0, chip or label.split(",")[0].split(" (")[0], color, size=8, h=20, pad=8)
            tws = [Tween(dur, grow_line(c, line, x0, y0, xe, ye), ease_in_out),
                   sprite.tween_to(xe, ye, dur)]

            def done():
                sprite.delete()
                mx, my = (x0 + xe) / 2, (y0 + ye) / 2
                c.create_text(mx, my - 8, text=label, fill=color if not lost else T.BAD, font=T.F(9, "bold"),
                              anchor="s")
                if lost:
                    c.create_text(xe + (10 if x1 > x0 else -10), ye, text=_("✘ потерян"), fill=T.BAD,
                                  font=T.F(9, "bold"), anchor="w" if x1 > x0 else "e")
                for idx, st in (states or {}).items():
                    self._state(idx, y0 if idx == a else y1, st)
                if rtt:
                    self._rtt_bracket()
            tws.append(later(dur, done))
            return tws
        return Step(text, action, title)

    def note(self, actor, note, text, title="", color=T.WARN, advance=24):
        def action():
            x, anchor = self._side(actor)
            y = self.y - 4
            item = self.c.create_text(x, y, text=note, fill=color, font=T.F(9, "bold"), width=200,
                                      anchor="ne" if anchor == "e" else "nw",
                                      justify="right" if anchor == "e" else "left")
            x1, y1, x2, y2 = self.c.bbox(item)
            self.y += max(advance, y2 - y1 + 8)
            return fade_in(self.c, [(item, "fill", color)], 500)
        return Step(text, action, title)

    def _rtt_bracket(self):
        self.rtt_n += 1
        y1, y2 = self.rtt_y, self.y - self.gap
        x = 26
        self.c.create_line(x + 8, y1, x, y1, x, y2, x + 8, y2, fill=T.ACCENT2, width=2)
        self.c.create_text(x - 6, (y1 + y2) / 2, text=f"RTT {self.rtt_n}", fill=T.ACCENT2, font=T.F(8, "bold"),
                           angle=90)
        self.rtt_y = self.y - self.gap + 4
