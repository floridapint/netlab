"""Страница урока: Теория · Анимации · Интерактив · Практика · Тест."""
from __future__ import annotations

import random
import tkinter as tk

from .. import theme as T
from ..core.questions import get_questions
from ..i18n import N_, _, content
from ..ui.animation import AnimationPlayer
from ..ui.richtext import RichText
from ..ui.trainers import QuizWidget
from ..ui.widgets import ScrollFrame, Segmented, Tabs, label


class SwitchPanel(tk.Frame):
    """Переключатель нескольких инструментов внутри вкладки (кэширует созданные)."""

    def __init__(self, master, items, make, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        self.items = items
        self.make = make
        self.frames = {}
        self.current = None
        if len(items) > 1:
            Segmented(self, [_(n) for n, _f in items], command=self.show).pack(anchor="w", pady=(0, 14))
        self.holder = tk.Frame(self, bg=bg)
        self.holder.pack(fill="both", expand=True)
        self.show(0)

    def show(self, i):
        if self.current is not None:
            self.frames[self.current].pack_forget()
        if i not in self.frames:
            self.frames[i] = self.make(self.holder, self.items[i][1])
        self.frames[i].pack(fill="both", expand=True)
        self.current = i


class LessonPage(tk.Frame):
    TABS = [N_("Теория"), N_("Анимации"), N_("Интерактив"), N_("Практика"), N_("Тест")]

    def __init__(self, master, app, lesson):
        super().__init__(master, bg=T.BG)
        self.app = app
        self.lesson = lesson
        head = tk.Frame(self, bg=T.BG)
        head.pack(fill="x", padx=28, pady=(18, 10))
        tk.Frame(head, bg=lesson.color, width=6, height=46).pack(side="left", padx=(0, 14))
        txt = tk.Frame(head, bg=T.BG)
        txt.pack(side="left")
        label(txt, _("УРОК {n}").format(n=lesson.number), 9, "bold", fg=lesson.color).pack(anchor="w")
        label(txt, _(lesson.title), 20, "bold").pack(anchor="w")
        label(head, _(lesson.subtitle), 10, fg=T.MUTED).pack(side="right", anchor="s")

        self.nb = Tabs(self, on_change=self._ensure, accent=lesson.color)
        self.nb.pack(fill="both", expand=True, padx=28, pady=(0, 16))
        self.built = set()
        self.tabs = [self.nb.add(_(name)) for name in self.TABS]

    def select_tab(self, i):
        self.nb.select(i, fire=False)
        self._ensure(i)

    def _ensure(self, i):
        if i in self.built:
            return
        self.built.add(i)
        getattr(self, f"_build_{i}")(self.tabs[i])

    # 0 — теория
    def _build_0(self, parent):
        rt = RichText(parent, height=20, padx=30, pady=20, size=11)
        rt.pack(fill="both", expand=True)
        rt.render(content("THEORY", self.lesson.key, self.lesson.theory))
        self.app.progress.mark_theory(self.lesson.key)

    # 1 — анимации
    def _build_1(self, parent):
        sf = ScrollFrame(parent)
        sf.pack(fill="both", expand=True)
        self.player = AnimationPlayer(sf.inner, self.lesson.scenarios,
                                      on_complete=lambda title: self.app.progress.mark_anim(self.lesson.key, title))
        self.player.pack(fill="both", expand=True, padx=18, pady=14)

    # 2 — интерактив
    def _build_2(self, parent):
        sf = ScrollFrame(parent)
        sf.pack(fill="both", expand=True)
        SwitchPanel(sf.inner, self.lesson.interactive, lambda p, f: f(p)).pack(fill="both", expand=True, padx=18, pady=14)

    # 3 — практика
    def _build_3(self, parent):
        sf = ScrollFrame(parent)
        sf.pack(fill="both", expand=True)

        def solved():
            self.app.progress.add_task(self.lesson.key)
        SwitchPanel(sf.inner, self.lesson.practice, lambda p, f: f(p, solved)).pack(fill="both", expand=True, padx=18,
                                                                                      pady=14)

    # 4 — тест
    def _build_4(self, parent):
        sf = ScrollFrame(parent)
        sf.pack(fill="both", expand=True)
        key = self.lesson.key

        def provider():
            qs = [dict(q, topic=key) for q in get_questions(key)]
            random.shuffle(qs)
            return qs[:10]

        QuizWidget(sf.inner, provider, title=_("Тест: {name}").format(name=_(self.lesson.title)),
                   on_finish=lambda ok, total, _pt: self.app.progress.set_quiz(key, ok / total)
                   ).pack(fill="both", expand=True, padx=18, pady=14)
