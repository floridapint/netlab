"""Базовые виджеты: плоские кнопки, переключатели, прокручиваемая область, журнал."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import theme as T


def parent_bg(w) -> str:
    try:
        return w.cget("bg")
    except (tk.TclError, AttributeError):
        return T.BG


def label(master, text="", size=10, weight="normal", fg=None, bg=None, mono=False, **kw):
    return tk.Label(master, text=text, font=T.F(size, weight, mono=mono), fg=fg or T.TEXT,
                    bg=bg or parent_bg(master), **kw)


def card(master, bg=None, border=None, **kw):
    return tk.Frame(master, bg=bg or T.CARD, highlightthickness=1, highlightbackground=border or T.BORDER,
                    highlightcolor=border or T.BORDER, **kw)


def entry(master, width=20, mono=True, size=11, textvariable=None):
    return tk.Entry(master, width=width, bg=T.PANEL2, fg=T.TEXT, insertbackground=T.TEXT, relief="flat",
                    font=T.F(size, mono=mono), highlightthickness=2, highlightbackground=T.BORDER,
                    highlightcolor=T.ACCENT, textvariable=textvariable, disabledbackground=T.PANEL,
                    disabledforeground=T.MUTED)


def checkbox(master, text, variable, command=None):
    bg = parent_bg(master)
    return tk.Checkbutton(master, text=text, variable=variable, command=command, bg=bg, fg=T.TEXT,
                          activebackground=bg, activeforeground=T.TEXT, selectcolor=T.PANEL2,
                          font=T.F(10), bd=0, highlightthickness=0, cursor="hand2")


class FlatButton(tk.Label):
    def __init__(self, master, text="", command=None, kind="secondary", bg=None, fg=None, size=10, bold=True,
                 padx=14, pady=6, anchor="center", **kw):
        pb = parent_bg(master)
        base = {
            "primary": (T.ACCENT, T.ON_ACCENT),
            "secondary": (T.PANEL2, T.TEXT),
            "ghost": (pb, T.MUTED),
            "good": (T.GOOD, T.ON_ACCENT),
            "danger": (T.BAD, T.ON_ACCENT),
            "warn": (T.WARN, T.ON_ACCENT),
        }[kind]
        self._bg = bg or base[0]
        self._fg = fg or base[1]
        super().__init__(master, text=text, bg=self._bg, fg=self._fg, font=T.F(size, "bold" if bold else "normal"),
                         padx=padx, pady=pady, cursor="hand2", anchor=anchor, bd=0, **kw)
        self.command = command
        self.enabled = True
        self._hover = False
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _hover_bg(self):
        return T.mix(self._bg, "#ffffff", 0.13)

    def _paint(self):
        if not self.enabled:
            self.configure(bg=T.mix(self._bg, T.BG, 0.55), fg=T.mix(self._fg, T.BG, 0.45), cursor="arrow")
        else:
            self.configure(bg=self._hover_bg() if self._hover else self._bg, fg=self._fg,
                           cursor="hand2" if self.command else "arrow")

    def _on_enter(self, _e):
        self._hover = True
        self._paint()

    def _on_leave(self, _e):
        self._hover = False
        self._paint()

    def _on_release(self, e):
        if not self.enabled or not self.command:
            return
        if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
            self.command()

    def set_enabled(self, flag: bool):
        self.enabled = flag
        self._paint()

    def set_colors(self, bg=None, fg=None):
        if bg:
            self._bg = bg
        if fg:
            self._fg = fg
        self._paint()

    def set_text(self, text):
        self.configure(text=text)


class Segmented(tk.Frame):
    """Ряд кнопок-переключателей (как вкладки)."""

    def __init__(self, master, options, command=None, index=0, size=10, bg=None, accent=None):
        super().__init__(master, bg=bg or parent_bg(master))
        self.command = command
        self.accent = accent or T.ACCENT
        self.buttons = []
        self.index = None
        for i, opt in enumerate(options):
            b = FlatButton(self, opt, command=lambda i=i: self.select(i), size=size, padx=12, pady=5)
            b.pack(side="left", padx=(0, 4))
            self.buttons.append(b)
        if options:
            self.select(index, fire=False)

    def select(self, i, fire=True):
        changed = self.index != i
        self.index = i
        for j, b in enumerate(self.buttons):
            b.set_colors(bg=self.accent if j == i else T.PANEL2, fg=T.ON_ACCENT if j == i else T.TEXT)
        if fire and changed and self.command:
            self.command(i)


class Tabs(tk.Frame):
    """Собственная панель вкладок (без рамок ttk). add(name) → frame; on_change(i) при переключении."""

    def __init__(self, master, on_change=None, accent=None, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        self.on_change = on_change
        self.accent = accent or T.ACCENT
        self.bar = tk.Frame(self, bg=bg)
        self.bar.pack(fill="x")
        tk.Frame(self, bg=T.BORDER, height=1).pack(fill="x")
        self.body = tk.Frame(self, bg=bg)
        self.body.pack(fill="both", expand=True)
        self.tabs = []   # (button, underline, frame)
        self.index = None

    def add(self, name):
        cell = tk.Frame(self.bar, bg=self.bar["bg"])
        cell.pack(side="left", padx=(0, 2))
        i = len(self.tabs)
        b = FlatButton(cell, name, command=lambda: self.select(i), kind="ghost", size=11, padx=18, pady=8)
        b.pack()
        line = tk.Frame(cell, bg=self.bar["bg"], height=3)
        line.pack(fill="x")
        frame = tk.Frame(self.body, bg=self.body["bg"])
        self.tabs.append((b, line, frame))
        if self.index is None:
            self.select(0, fire=False)
        return frame

    def select(self, i, fire=True):
        if self.index is not None and self.index != i:
            self.tabs[self.index][2].pack_forget()
        self.index = i
        for j, (b, line, frame) in enumerate(self.tabs):
            on = j == i
            b.set_colors(fg=T.TEXT if on else T.MUTED)
            line.configure(bg=self.accent if on else self.bar["bg"])
        self.tabs[i][2].pack(fill="both", expand=True)
        if fire and self.on_change:
            self.on_change(i)


class ScrollFrame(tk.Frame):
    """Вертикально прокручиваемый контейнер. Содержимое кладите в .inner"""

    _installed = False

    def __init__(self, master, bg=None, **kw):
        bg = bg or T.BG
        super().__init__(master, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.canvas._scrollframe = self
        self.inner._scrollframe = self
        root = self.winfo_toplevel()
        if ScrollFrame._installed is not root:
            ScrollFrame._installed = root
            root.bind_all("<MouseWheel>", ScrollFrame._dispatch, add="+")
            root.bind_all("<Button-4>", ScrollFrame._dispatch, add="+")
            root.bind_all("<Button-5>", ScrollFrame._dispatch, add="+")

    @staticmethod
    def _dispatch(event):
        w = event.widget
        while isinstance(w, tk.Misc):
            if isinstance(w, (tk.Text, tk.Listbox, ttk.Treeview)):
                return  # у этих виджетов своя прокрутка
            sf = getattr(w, "_scrollframe", None)
            if sf is not None:
                sf.scroll(event)
                return
            w = w.master

    def scroll(self, event):
        if self.inner.winfo_reqheight() <= self.canvas.winfo_height():
            return
        if getattr(event, "num", None) == 4:
            step = -2
        elif getattr(event, "num", None) == 5:
            step = 2
        else:
            step = -2 if event.delta > 0 else 2
        self.canvas.yview_scroll(step, "units")

    def to_top(self):
        self.canvas.yview_moveto(0)


class LogView(tk.Frame):
    """Журнал событий с цветными строками."""

    COLORS = {"info": T.MUTED, "recv": T.GOOD, "send": T.ACCENT, "error": T.BAD, "warn": T.WARN, "plain": T.TEXT}

    def __init__(self, master, title="", height=10, width=40, bg=None):
        bg = bg or T.CARD
        super().__init__(master, bg=bg, highlightthickness=1, highlightbackground=T.BORDER)
        if title:
            label(self, title, 10, "bold", fg=T.MUTED, bg=bg).pack(anchor="w", padx=10, pady=(8, 2))
        self.text = tk.Text(self, bg=bg, fg=T.TEXT, relief="flat", bd=0, wrap="word", height=height, width=width,
                            font=T.F(9, mono=True), padx=10, pady=6, highlightthickness=0, insertwidth=0,
                            cursor="arrow", takefocus=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set, state="disabled")
        sb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        for k, c in self.COLORS.items():
            self.text.tag_configure(k, foreground=c)
        self.text.tag_configure("time", foreground=T.DIM)

    def append(self, text, kind="plain", stamp=None):
        self.text.configure(state="normal")
        if stamp:
            self.text.insert("end", stamp + " ", "time")
        self.text.insert("end", text + "\n", kind)
        self.text.see("end")
        self.text.configure(state="disabled")

    def set(self, text, kind="plain"):
        self.clear()
        self.text.configure(state="normal")
        self.text.insert("end", text, kind)
        self.text.configure(state="disabled")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")


def section_title(master, title, subtitle="", bg=None):
    f = tk.Frame(master, bg=bg or parent_bg(master))
    label(f, title, 15, "bold").pack(anchor="w")
    if subtitle:
        label(f, subtitle, 10, fg=T.MUTED, wraplength=900, justify="left").pack(anchor="w", pady=(2, 0))
    return f
