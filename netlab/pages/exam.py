"""Итоговый экзамен по всем темам."""
from __future__ import annotations

import random
import tkinter as tk

from .. import theme as T
from ..core.questions import QUESTIONS, TOPIC_NAMES, get_questions
from ..i18n import _
from ..ui.trainers import QuizWidget
from ..ui.widgets import FlatButton, ScrollFrame, Segmented, card, label


class ExamPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=T.BG)
        self.app = app
        self.sf = ScrollFrame(self)
        self.sf.pack(fill="both", expand=True)
        self.body = tk.Frame(self.sf.inner, bg=T.BG)
        self.body.pack(fill="both", expand=True, padx=34, pady=24)
        self.count = 20
        self._intro()

    def _clear(self):
        for w in self.body.winfo_children():
            w.destroy()

    def _intro(self):
        self._clear()
        label(self.body, _("ИТОГОВЫЙ ЭКЗАМЕН"), 9, "bold", fg=T.WARN).pack(anchor="w")
        label(self.body, _("Проверьте себя по всем темам"), 22, "bold").pack(anchor="w", pady=(2, 6))
        total = sum(len(v) for v in QUESTIONS.values())
        label(self.body, _("Вопросы случайно выбираются из банка ({n} шт.) по всем шести темам, варианты ответов "
                           "перемешиваются. После каждого ответа — объяснение, в конце — разбивка по темам и разбор "
                           "ошибок.").format(n=total), 11, fg=T.MUTED, wraplength=900, justify="left").pack(anchor="w")
        c = card(self.body, bg=T.CARD)
        c.pack(fill="x", pady=18)
        label(c, _("Количество вопросов"), 11, "bold", bg=T.CARD).pack(anchor="w", padx=20, pady=(16, 8))
        opts = [10, 20, 30, total]
        self.count = 20
        Segmented(c, ["10", "20", "30", _("Все ({n})").format(n=total)], index=1, bg=T.CARD,
                  command=lambda i: setattr(self, "count", opts[i])).pack(anchor="w", padx=20)
        best = self.app.progress.data.get("exam_best", 0)
        text = _("Лучший результат: {p}%").format(p=round(best * 100)) if best else _("Вы ещё не сдавали экзамен.")
        label(c, text, 10, fg=T.MUTED, bg=T.CARD).pack(anchor="w", padx=20, pady=(12, 0))
        FlatButton(c, _("Начать экзамен  →"), self._start, kind="warn", size=11, padx=20, pady=9).pack(
            anchor="w", padx=20, pady=(14, 18))

    def _start(self):
        self._clear()

        def provider():
            # равномерно по темам, затем перемешать
            pool = {k: random.sample(get_questions(k), len(QUESTIONS[k])) for k in QUESTIONS}
            out = []
            while len(out) < self.count and any(pool.values()):
                for k in pool:
                    if pool[k] and len(out) < self.count:
                        out.append(dict(pool[k].pop(), topic=k))
            random.shuffle(out)
            return out

        QuizWidget(self.body, provider, title=_("Итоговый экзамен"), topic_names=TOPIC_NAMES,
                   on_finish=lambda ok, total, _pt: self.app.progress.set_exam(ok / total)).pack(fill="both", expand=True)
        FlatButton(self.body, _("← К настройкам экзамена"), self._intro, kind="ghost").pack(anchor="w", pady=(4, 0))
        self.sf.to_top()
