"""Главная страница: приветствие, карточки уроков с прогрессом."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .. import theme as T
from ..i18n import _
from ..lessons import LESSONS
from ..ui.widgets import FlatButton, ScrollFrame, label


class HomePage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=T.BG)
        self.app = app
        self.sf = ScrollFrame(self)
        self.sf.pack(fill="both", expand=True)
        self.body = self.sf.inner
        self.bars = {}
        self._build()
        app.progress.listeners.append(self.refresh)
        self.bind("<Destroy>", lambda e: e.widget is self and self.refresh in app.progress.listeners
                  and app.progress.listeners.remove(self.refresh))

    def _build(self):
        b = self.body
        hero = tk.Frame(b, bg=T.BG)
        hero.pack(fill="x", padx=34, pady=(28, 6))
        label(hero, _("Сети — наглядно и на практике"), 24, "bold").pack(anchor="w")
        label(hero, _("Интерактивная лаборатория: модели OSI и TCP/IP, протоколы IP, UDP, TCP и SSL/TLS. "
                      "В каждом уроке — теория, пошаговые анимации, интерактивные схемы, практика с живыми сокетами "
                      "и тест с разбором ошибок."), 11, fg=T.MUTED, wraplength=980, justify="left").pack(anchor="w",
                                                                                                      pady=(6, 0))
        how = tk.Frame(b, bg=T.BG)
        how.pack(fill="x", padx=34, pady=(16, 6))
        steps = ((_("1 · Теория"), _("коротко и по делу")), (_("2 · Анимации"), _("пошагово, с паузой и перемоткой")),
                 (_("3 · Интерактив"), _("схемы и калькуляторы")), (_("4 · Практика"), _("задачи и живые сокеты")),
                 (_("5 · Тест"), _("проверка с объяснениями")))
        for t, d in steps:
            f = tk.Frame(how, bg=T.PANEL, highlightthickness=1, highlightbackground=T.BORDER)
            f.pack(side="left", padx=(0, 8), fill="y")
            label(f, t, 10, "bold", fg=T.ACCENT, bg=T.PANEL).pack(anchor="w", padx=12, pady=(8, 0))
            label(f, d, 9, fg=T.MUTED, bg=T.PANEL).pack(anchor="w", padx=12, pady=(0, 8))

        label(b, _("УРОКИ  ·  рекомендуемый порядок — слева направо, сверху вниз"), 9, "bold", fg=T.MUTED).pack(
            anchor="w", padx=34, pady=(18, 6))
        grid = tk.Frame(b, bg=T.BG)
        grid.pack(fill="x", padx=28)
        for i, lesson in enumerate(LESSONS):
            self._card(grid, lesson).grid(row=i // 3, column=i % 3, sticky="nsew", padx=6, pady=6)
        for i in range(3):
            grid.columnconfigure(i, weight=1, uniform="c")

        extra = tk.Frame(b, bg=T.BG)
        extra.pack(fill="x", padx=28, pady=(6, 0))
        exam, self.exam_lbl = self._wide(extra, _("★  Итоговый экзамен"), "", T.WARN, lambda: self.app.show("exam"))
        exam.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        ref, _lbl = self._wide(extra, _("☰  Справочник"), _("Порты, команды, сравнения протоколов и глоссарий — всё на "
                                                           "одной странице."), T.ACCENT2, lambda: self.app.show("ref"))
        ref.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        extra.columnconfigure(0, weight=1, uniform="e")
        extra.columnconfigure(1, weight=1, uniform="e")

        foot = tk.Frame(b, bg=T.BG)
        foot.pack(fill="x", padx=34, pady=(16, 24))
        label(foot, _("Прогресс сохраняется в {path}").format(path=self.app.progress.path), 9, fg=T.DIM).pack(side="left")
        FlatButton(foot, _("Сбросить прогресс"), self._reset, kind="ghost", size=9).pack(side="right")
        self.refresh()

    def _card(self, parent, lesson):
        f = tk.Frame(parent, bg=T.CARD, highlightthickness=1, highlightbackground=T.BORDER, cursor="hand2")
        tk.Frame(f, bg=lesson.color, height=4).pack(fill="x")
        inner = tk.Frame(f, bg=T.CARD)
        inner.pack(fill="both", expand=True, padx=18, pady=14)
        label(inner, _("УРОК {n}").format(n=lesson.number), 9, "bold", fg=lesson.color, bg=T.CARD).pack(anchor="w")
        label(inner, _(lesson.title), 15, "bold", bg=T.CARD).pack(anchor="w", pady=(2, 4))
        label(inner, _(lesson.subtitle), 10, fg=T.MUTED, bg=T.CARD, wraplength=290, justify="left").pack(anchor="w")
        meta = label(inner, "", 9, fg=T.DIM, bg=T.CARD)
        meta.pack(anchor="w", pady=(10, 2))
        row = tk.Frame(inner, bg=T.CARD)
        row.pack(fill="x")
        bar = ttk.Progressbar(row, maximum=100, length=200)
        bar.pack(side="left", fill="x", expand=True)
        pct = label(row, "0%", 10, "bold", bg=T.CARD, width=5)
        pct.pack(side="left", padx=(8, 0))
        self.bars[lesson.key] = (bar, pct, meta, lesson)

        def go(_e=None, k=lesson.key):
            self.app.show(k)
        for w in (f, inner) + tuple(inner.winfo_children()):
            if not isinstance(w, ttk.Progressbar):
                w.bind("<Button-1>", go)
        f.bind("<Enter>", lambda e: f.configure(highlightbackground=lesson.color))
        f.bind("<Leave>", lambda e: f.configure(highlightbackground=T.BORDER))
        return f

    def _wide(self, parent, title, desc, color, cmd):
        f = tk.Frame(parent, bg=T.CARD, highlightthickness=1, highlightbackground=T.BORDER, cursor="hand2")
        inner = tk.Frame(f, bg=T.CARD)
        inner.pack(fill="both", expand=True, padx=18, pady=14)
        label(inner, title, 13, "bold", fg=color, bg=T.CARD).pack(anchor="w")
        d = label(inner, desc, 10, fg=T.MUTED, bg=T.CARD, wraplength=440, justify="left")
        d.pack(anchor="w", pady=(4, 0))
        for w in (f, inner) + tuple(inner.winfo_children()):
            w.bind("<Button-1>", lambda _e: cmd())
        f.bind("<Enter>", lambda e: f.configure(highlightbackground=color))
        f.bind("<Leave>", lambda e: f.configure(highlightbackground=T.BORDER))
        return f, d

    def refresh(self):
        p = self.app.progress
        try:
            for key, (bar, pct, meta, lesson) in self.bars.items():
                value = p.percent(key, len(lesson.scenarios))
                e = p.lesson(key)
                bar.configure(value=value, style="Good.Horizontal.TProgressbar" if value >= 80 else "Horizontal.TProgressbar")
                pct.configure(text=f"{value}%")
                meta.configure(text=_("анимаций {a}/{n}  ·  задач {t}  ·  тест {q}%").format(
                    a=len(e["anims"]), n=len(lesson.scenarios), t=e["tasks"], q=round(e["quiz"] * 100)))
            best = p.data.get("exam_best", 0)
            text = _("Вопросы по всем темам вперемешку с разбивкой результата по темам.")
            if best:
                text += "  " + _("Лучший результат: {p}%.").format(p=round(best * 100))
            self.exam_lbl.configure(text=text)
        except tk.TclError:
            pass

    def _reset(self):
        if messagebox.askyesno(_("Сброс прогресса"), _("Удалить весь сохранённый прогресс? Это нельзя отменить."),
                               parent=self):
            self.app.progress.reset()
