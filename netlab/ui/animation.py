"""Движок пошаговых анимаций на Canvas.

Сценарий (Scenario) рисует сцену в build() и возвращает список шагов (Step) в steps().
Каждый шаг — текст-пояснение + action(), который возвращает твины (Tween).
Плеер умеет: играть/пауза, шаг вперёд/назад, переход к любому шагу, скорость.
Шаг назад реализован перестройкой сцены и мгновенным проигрыванием предыдущих шагов.
"""
from __future__ import annotations

import time
import tkinter as tk

from .. import theme as T
from ..i18n import N_, _
from .richtext import RichText
from .widgets import FlatButton, Segmented, label

W, H = 880, 440


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def ease_out(t):
    return 1 - (1 - t) ** 3


def linear(t):
    return t


class Tween:
    def __init__(self, duration, fn, ease=ease_in_out, delay=0):
        self.duration = duration
        self.fn = fn
        self.ease = ease
        self.delay = delay
        self.elapsed = 0.0
        self.done = False

    def advance(self, dt):
        if self.done:
            return True
        self.elapsed += dt
        local = self.elapsed - self.delay
        if local < 0:
            return False
        t = 1.0 if self.duration <= 0 else min(1.0, local / self.duration)
        self.fn(self.ease(t))
        if t >= 1.0:
            self.done = True
        return self.done

    def finish(self):
        if not self.done:
            self.fn(1.0)
            self.done = True

    @property
    def end(self):
        return self.delay + self.duration


def later(delay, func):
    """Вызвать func один раз через delay мс внутри шага."""
    return Tween(0, lambda _t: func(), linear, delay)


def _flatten(res):
    out = []
    if res is None:
        return out
    if isinstance(res, Tween):
        return [res]
    for r in res:
        out.extend(_flatten(r))
    return out


class Step:
    def __init__(self, text, action=None, title=""):
        self.text = text
        self.action = action
        self.title = title


class Scenario:
    title = N_("Сценарий")
    intro = N_("Нажмите ▶, чтобы начать.")

    def build(self, c: tk.Canvas):
        pass

    def steps(self):
        return []


class AnimationPlayer(tk.Frame):
    def __init__(self, master, scenarios, on_complete=None, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        self.scenario_classes = scenarios
        self.on_complete = on_complete
        self.speed = 1.0
        self.playing = False
        self.tweens = []
        self.index = 0
        self.steps = []
        self._tick_job = None
        self._auto_job = None
        self._last = 0.0

        top = tk.Frame(self, bg=bg)
        top.pack(fill="x", pady=(0, 8))
        self.selector = None
        if len(scenarios) > 1:
            label(top, _("Сценарий:"), 10, fg=T.MUTED).pack(side="left", padx=(0, 8))
            self.selector = Segmented(top, [_(s.title) for s in scenarios], command=self.load)
            self.selector.pack(side="left")
        else:
            label(top, _(scenarios[0].title), 12, "bold").pack(side="left")

        holder = tk.Frame(self, bg=T.BORDER, padx=1, pady=1)
        holder.pack(anchor="w")
        self.canvas = tk.Canvas(holder, width=W, height=H, bg=T.CANVAS, highlightthickness=0, bd=0)
        self.canvas.pack()

        ctrl = tk.Frame(self, bg=bg)
        ctrl.pack(fill="x", pady=(8, 4))
        self.b_reset = FlatButton(ctrl, _("⟲  Сначала"), self.reset)
        self.b_back = FlatButton(ctrl, _("◀  Назад"), self.back)
        self.b_play = FlatButton(ctrl, _("▶  Играть"), self.toggle, kind="primary", width=13)
        self.b_next = FlatButton(ctrl, _("Шаг  ▶"), self.forward)
        for b in (self.b_reset, self.b_back, self.b_play, self.b_next):
            b.pack(side="left", padx=(0, 6))
        label(ctrl, _("Скорость:"), 10, fg=T.MUTED).pack(side="left", padx=(16, 6))
        speeds = [0.5, 1.0, 1.5, 2.0]
        Segmented(ctrl, [f"{s:g}×" for s in speeds], index=1, size=9,
                  command=lambda i: setattr(self, "speed", speeds[i])).pack(side="left")
        self.dots = tk.Canvas(ctrl, height=22, width=260, bg=bg, highlightthickness=0)
        self.dots.pack(side="right")
        self.dots.bind("<Button-1>", self._dot_click)

        self.step_label = label(self, "", 10, "bold", fg=T.ACCENT)
        self.step_label.pack(anchor="w", pady=(4, 0))
        self.info = RichText(self, height=4, scroll=True, padx=0, pady=4, size=11, width=100)
        self.info.pack(fill="x")

        self.bind("<Destroy>", self._on_destroy)
        self.load(0)

    # ------------------------------------------------------------------ управление
    def load(self, idx):
        if self.selector is not None and self.selector.index != idx:
            self.selector.select(idx, fire=False)
        self.scenario = self.scenario_classes[idx]()
        self.playing = False
        self._rebuild(0)

    def _cancel_jobs(self):
        for job in (self._tick_job, self._auto_job):
            if job:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
        self._tick_job = self._auto_job = None

    def _rebuild(self, target):
        self._cancel_jobs()
        self.tweens = []
        c = self.canvas
        c.delete("all")
        self.scenario.build(c)
        self.steps = self.scenario.steps()
        for i in range(target):
            st = self.steps[i]
            tws = _flatten(st.action() if st.action else None)
            for tw in sorted(tws, key=lambda t: t.end):
                tw.finish()
        self.index = target
        if target == 0:
            self._show_text(None)
        else:
            self._show_text(self.steps[target - 1], target - 1)
        self._update_controls()

    def _show_text(self, step, i=None):
        if step is None:
            self.step_label.configure(text=_("Введение · шагов: {n}").format(n=len(self.steps)))
            self.info.render(_(self.scenario.intro))
        else:
            title = f" — {step.title}" if step.title else ""
            self.step_label.configure(text=_("Шаг {i} из {n}").format(i=i + 1, n=len(self.steps)) + title)
            self.info.render(step.text)

    def _update_controls(self):
        if self.playing:
            text = _("⏸  Пауза")
        elif self.index >= len(self.steps) and not self.tweens:
            text = _("⟲  Заново")
        else:
            text = _("▶  Играть")
        self.b_play.set_text(text)
        self.b_back.set_enabled(self.index > 0 or bool(self.tweens))
        self.b_next.set_enabled(self.index < len(self.steps) or bool(self.tweens))
        self._draw_dots()

    def _draw_dots(self):
        d = self.dots
        d.delete("all")
        n = len(self.steps)
        if not n:
            return
        gap = min(18, 250 / n)
        r = min(5, gap / 2 - 1)
        x0 = 260 - gap * n
        current = self.index if self.tweens else self.index - 1
        for i in range(n):
            x = x0 + gap * i + gap / 2
            if i < self.index:
                fill = T.ACCENT
            elif i == current or (self.tweens and i == self.index):
                fill = T.WARN
            else:
                fill = T.PANEL2
            d.create_oval(x - r, 11 - r, x + r, 11 + r, fill=fill, outline="")
        self._dot_geom = (x0, gap)

    def _dot_click(self, e):
        if not getattr(self, "_dot_geom", None) or not self.steps:
            return
        x0, gap = self._dot_geom
        i = int((e.x - x0) // gap)
        if 0 <= i < len(self.steps):
            self.playing = False
            self._rebuild(i + 1)

    def toggle(self):
        if self.playing:
            self.playing = False
            self._cancel_auto()
            self._update_controls()
            return
        if self.index >= len(self.steps) and not self.tweens:
            self._rebuild(0)
        self.playing = True
        self._update_controls()
        if not self.tweens:
            self._start_step()

    def _cancel_auto(self):
        if self._auto_job:
            try:
                self.after_cancel(self._auto_job)
            except tk.TclError:
                pass
            self._auto_job = None

    def forward(self):
        self._cancel_auto()
        if self.tweens:
            for tw in sorted(self.tweens, key=lambda t: t.end):
                tw.finish()
            self.tweens = []
            self._step_finished()
        elif self.index < len(self.steps):
            self._start_step()

    def back(self):
        self.playing = False
        target = self.index if self.tweens else max(0, self.index - 1)
        self._rebuild(target)

    def reset(self):
        self.playing = False
        self._rebuild(0)

    # ------------------------------------------------------------------ цикл
    def _start_step(self):
        if self.index >= len(self.steps):
            return
        st = self.steps[self.index]
        self._show_text(st, self.index)
        self.tweens = _flatten(st.action() if st.action else None)
        self._update_controls()
        if not self.tweens:
            self._step_finished()
            return
        self._last = time.perf_counter()
        if not self._tick_job:
            self._tick_job = self.after(15, self._tick)

    def _tick(self):
        self._tick_job = None
        now = time.perf_counter()
        dt = (now - self._last) * 1000 * self.speed
        self._last = now
        for tw in list(self.tweens):
            tw.advance(dt)
        if self.tweens and all(t.done for t in self.tweens):
            self.tweens = []
            self._step_finished()
        if self.tweens:
            self._tick_job = self.after(15, self._tick)

    def _step_finished(self):
        self.index += 1
        if self.index >= len(self.steps):
            self.playing = False
            if self.on_complete:
                self.on_complete(self.scenario.title)
        elif self.playing:
            text = self.steps[self.index - 1].text
            wait = max(1400, min(6500, len(text) * 32)) / self.speed
            self._auto_job = self.after(int(wait), self._auto_next)
        self._update_controls()

    def _auto_next(self):
        self._auto_job = None
        if self.playing:
            self._start_step()

    def _on_destroy(self, e):
        if e.widget is self:
            self._cancel_jobs()

    # ------------------------------------------------------------------ для самопроверки
    def run_all_instantly(self):
        for i in range(len(self.scenario_classes)):
            self.load(i)
            self._rebuild(len(self.steps))
