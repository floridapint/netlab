"""Тренажёры: тест с вариантами, задачи с полями ввода, «определи уровень OSI»."""
from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk

from .. import theme as T
from ..i18n import _
from .richtext import RichText
from .widgets import FlatButton, Segmented, card, entry, label


class QuizWidget(tk.Frame):
    """provider() -> список вопросов {"q", "options" (правильный первый), "explain", ["topic"]}."""

    def __init__(self, master, provider, on_finish=None, title="", bg=None, topic_names=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        self.bg = bg
        self.provider = provider
        self.on_finish = on_finish
        self.title = title or _("Тест")
        self.topic_names = topic_names or {}
        self.body = tk.Frame(self, bg=bg)
        self.body.pack(fill="both", expand=True)
        self.start()

    def _clear(self):
        for w in self.body.winfo_children():
            w.destroy()

    def _topic(self, key):
        return _(self.topic_names.get(key, key))

    def start(self):
        self._clear()
        self.questions = self.provider()
        self.i = 0
        self.correct = 0
        self.mistakes = []
        self.per_topic = {}

        head = tk.Frame(self.body, bg=self.bg)
        head.pack(fill="x")
        label(head, self.title, 15, "bold").pack(side="left")
        self.counter = label(head, "", 10, fg=T.MUTED)
        self.counter.pack(side="right")
        self.bar = ttk.Progressbar(self.body, maximum=len(self.questions), length=820)
        self.bar.pack(fill="x", pady=(6, 14))

        self.qcard = card(self.body, bg=T.CARD)
        self.qcard.pack(fill="x")
        self.topic_lbl = label(self.qcard, "", 9, "bold", fg=T.ACCENT2, bg=T.CARD)
        self.topic_lbl.pack(anchor="w", padx=20, pady=(14, 0))
        self.q_lbl = label(self.qcard, "", 14, "bold", bg=T.CARD, wraplength=820, justify="left")
        self.q_lbl.pack(anchor="w", padx=20, pady=(4, 12))
        self.opts = tk.Frame(self.qcard, bg=T.CARD)
        self.opts.pack(fill="x", padx=20, pady=(0, 16))

        self.feedback = label(self.body, "", 12, "bold", wraplength=900, justify="left")
        self.feedback.pack(anchor="w", pady=(12, 0))
        self.explain = RichText(self.body, height=4, scroll=False, padx=0, pady=2, size=11, width=90)
        self.explain.pack(fill="x")
        nav = tk.Frame(self.body, bg=self.bg)
        nav.pack(fill="x", pady=8)
        self.b_next = FlatButton(nav, _("Далее  →"), self._next, kind="primary")
        self._show()

    def _count_text(self):
        return _("Вопрос {i} из {n}  ·  верно: {ok}").format(i=self.i + 1, n=len(self.questions), ok=self.correct)

    def _show(self):
        q = self.questions[self.i]
        self.counter.configure(text=self._count_text())
        self.bar.configure(value=self.i)
        topic = q.get("topic")
        self.topic_lbl.configure(text=self._topic(topic).upper() if topic and self.topic_names else "")
        self.q_lbl.configure(text=q["q"])
        for w in self.opts.winfo_children():
            w.destroy()
        options = [(t, j == 0) for j, t in enumerate(q["options"])]
        random.shuffle(options)
        self.buttons = []
        for k, (text, ok) in enumerate(options):
            b = FlatButton(self.opts, f"{k + 1}.   {text}", anchor="w", bold=False, size=11, padx=16, pady=9,
                           wraplength=780, justify="left")
            b.command = (lambda b=b, ok=ok: self._answer(b, ok))
            b.pack(fill="x", pady=3)
            self.buttons.append((b, ok))
        self.answered = False
        self.feedback.configure(text="")
        self.explain.set_plain("")
        self.b_next.pack_forget()

    def _answer(self, btn, ok):
        if self.answered:
            return
        self.answered = True
        q = self.questions[self.i]
        topic = q.get("topic", "")
        good, total = self.per_topic.get(topic, (0, 0))
        self.per_topic[topic] = (good + ok, total + 1)
        for b, is_ok in self.buttons:
            b.command = None
            if is_ok:
                b.set_colors(bg=T.mix(T.GOOD, T.CARD, 0.35), fg=T.ON_ACCENT)
            elif b is btn:
                b.set_colors(bg=T.mix(T.BAD, T.CARD, 0.35), fg=T.ON_ACCENT)
            else:
                b.set_colors(bg=T.mix(T.PANEL2, T.CARD, 0.5), fg=T.DIM)
        if ok:
            self.correct += 1
            self.feedback.configure(text=_("✔  Верно!"), fg=T.GOOD)
        else:
            self.mistakes.append(q)
            self.feedback.configure(text=_("✘  Неверно. Правильный ответ: {a}").format(a=q["options"][0]), fg=T.BAD)
        self.explain.render(q["explain"])
        self.counter.configure(text=self._count_text())
        last = self.i == len(self.questions) - 1
        self.b_next.set_text(_("Результаты  →") if last else _("Далее  →"))
        self.b_next.pack(side="left")

    def _next(self):
        self.i += 1
        if self.i >= len(self.questions):
            self._results()
        else:
            self._show()

    def _results(self):
        self._clear()
        total = len(self.questions)
        ratio = self.correct / total if total else 0
        color = T.GOOD if ratio >= 0.8 else T.WARN if ratio >= 0.5 else T.BAD
        msg = (_("Отлично! Тема освоена.") if ratio >= 0.8 else
               _("Неплохо, но стоит повторить теорию и анимации.") if ratio >= 0.5 else
               _("Пересмотрите теорию и анимации — и попробуйте снова."))
        c = card(self.body, bg=T.CARD)
        c.pack(fill="x")
        label(c, _("Результат"), 11, "bold", fg=T.MUTED, bg=T.CARD).pack(anchor="w", padx=24, pady=(18, 0))
        label(c, f"{round(ratio * 100)}%", 40, "bold", fg=color, bg=T.CARD).pack(anchor="w", padx=22)
        label(c, _("{ok} из {n} верно · {msg}").format(ok=self.correct, n=total, msg=msg), 12, bg=T.CARD).pack(
            anchor="w", padx=24, pady=(0, 18))

        if len(self.per_topic) > 1:
            pt = card(self.body, bg=T.CARD)
            pt.pack(fill="x", pady=(10, 0))
            label(pt, _("По темам"), 11, "bold", bg=T.CARD).pack(anchor="w", padx=24, pady=(14, 6))
            for topic, (good, cnt) in self.per_topic.items():
                row = tk.Frame(pt, bg=T.CARD)
                row.pack(fill="x", padx=24, pady=2)
                label(row, self._topic(topic), 10, bg=T.CARD, width=18, anchor="w").pack(side="left")
                style = "Good.Horizontal.TProgressbar" if good / cnt >= 0.8 else "Warn.Horizontal.TProgressbar"
                ttk.Progressbar(row, maximum=cnt, value=good, length=360, style=style).pack(side="left", padx=10)
                label(row, f"{good}/{cnt}", 10, fg=T.MUTED, bg=T.CARD).pack(side="left")
            tk.Frame(pt, bg=T.CARD, height=12).pack()

        if self.mistakes:
            label(self.body, _("Разбор ошибок"), 13, "bold").pack(anchor="w", pady=(16, 4))
            rt = RichText(self.body, height=min(14, 3 + 3 * len(self.mistakes)), padx=0, pady=0, size=10, width=90)
            rt.pack(fill="x")
            rt.render("\n".join(f"**{m['q']}**\n> {m['options'][0]}\n{m['explain']}\n" for m in self.mistakes))
        FlatButton(self.body, _("⟲  Пройти ещё раз"), self.start, kind="primary").pack(anchor="w", pady=14)
        if self.on_finish:
            self.on_finish(self.correct, total, self.per_topic)


class TaskTrainer(tk.Frame):
    """Бесконечные задачи с полями ввода. generators: [(название, fn(rng) -> Task)]."""

    def __init__(self, master, title, description, generators, on_solved=None, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        self.bg = bg
        self.generators = generators
        self.on_solved = on_solved
        self.rng = random.Random()
        self.kind = 0
        self.solved_count = 0
        self.streak = 0

        label(self, title, 15, "bold").pack(anchor="w")
        label(self, description, 10, fg=T.MUTED, wraplength=900, justify="left").pack(anchor="w", pady=(2, 10))
        if len(generators) > 1:
            Segmented(self, [g[0] for g in generators], command=self._set_kind).pack(anchor="w", pady=(0, 10))

        self.box = card(self, bg=T.CARD)
        self.box.pack(fill="x")
        self.task_text = RichText(self.box, bg=T.CARD, height=2, scroll=False, padx=20, pady=12, size=12, width=90)
        self.task_text.pack(fill="x")
        self.fields_frame = tk.Frame(self.box, bg=T.CARD)
        self.fields_frame.pack(fill="x", padx=20, pady=(0, 12))
        btns = tk.Frame(self.box, bg=T.CARD)
        btns.pack(fill="x", padx=20, pady=(0, 16))
        FlatButton(btns, _("✔  Проверить  (Enter)"), self.check, kind="primary").pack(side="left")
        FlatButton(btns, _("Показать решение"), self.reveal).pack(side="left", padx=8)
        FlatButton(btns, _("Новое задание  →"), self.new_task).pack(side="left")
        self.stats = label(btns, "", 10, fg=T.MUTED, bg=T.CARD)
        self.stats.pack(side="right")

        self.feedback = label(self, "", 12, "bold")
        self.feedback.pack(anchor="w", pady=(12, 2))
        self.explain = RichText(self, height=8, scroll=True, padx=0, pady=2, size=11, width=90)
        self.explain.pack(fill="x")
        self.new_task()

    def _set_kind(self, i):
        self.kind = i
        self.new_task()

    def _update_stats(self):
        self.stats.configure(text=_("Решено: {n}   ·   Серия: {s}").format(n=self.solved_count, s=self.streak))

    def new_task(self):
        self.task = self.generators[self.kind][1](self.rng)
        self.task_text.render(self.task.text)
        for w in self.fields_frame.winfo_children():
            w.destroy()
        self.entries = []
        for r, f in enumerate(self.task.fields):
            label(self.fields_frame, f.label, 11, bg=T.CARD, anchor="w").grid(row=r, column=0, sticky="w", pady=4,
                                                                              padx=(0, 16))
            e = entry(self.fields_frame, width=22)
            e.grid(row=r, column=1, sticky="w", pady=4)
            if f.placeholder:
                label(self.fields_frame, f.placeholder, 9, fg=T.DIM, bg=T.CARD).grid(row=r, column=2, sticky="w", padx=10)
            e.bind("<Return>", lambda _e: self.check())
            self.entries.append(e)
        if self.entries:
            self.entries[0].focus_set()
        self.feedback.configure(text="")
        self.explain.set_plain("")
        self.solved = False
        self.revealed = False
        self._update_stats()

    def check(self):
        all_ok = True
        for f, e in zip(self.task.fields, self.entries):
            ok = f.check(e.get())
            color = T.GOOD if ok else T.BAD
            e.configure(highlightbackground=color, highlightcolor=color)
            all_ok &= ok
        if all_ok:
            self.feedback.configure(text=_("✔  Всё верно!  Жмите «Новое задание»."), fg=T.GOOD)
            if not self.solved and not self.revealed:
                self.solved = True
                self.solved_count += 1
                self.streak += 1
                if self.on_solved:
                    self.on_solved()
            self.explain.render(self.task.explain)
        else:
            self.feedback.configure(text=_("✘  Есть ошибки — поля с неверным ответом подсвечены красным."), fg=T.BAD)
            self.streak = 0
        self._update_stats()

    def reveal(self):
        self.revealed = True
        self.streak = 0
        answers = "\n".join(f"- {f.label}: **{f.answer}**" for f in self.task.fields)
        self.feedback.configure(text=_("Решение:"), fg=T.WARN)
        self.explain.render(answers + "\n\n" + self.task.explain)
        self._update_stats()


class ClassifyTrainer(tk.Frame):
    """Определи уровень OSI: items = [(предмет, уровень, пояснение)] — тексты переводятся при показе."""

    def __init__(self, master, items, on_solved=None, bg=None):
        bg = bg or T.BG
        super().__init__(master, bg=bg)
        self.items = list(items)
        self.on_solved = on_solved
        self.deck = []
        self.score = 0
        self.total = 0
        self.streak = 0
        self._job = None

        label(self, _("Определи уровень OSI"), 15, "bold").pack(anchor="w")
        label(self, _("К какому уровню модели OSI относится протокол, устройство или понятие? Правильный ответ — "
                      "сразу следующий вопрос. Ошибся — читай пояснение."), 10, fg=T.MUTED, wraplength=900,
              justify="left").pack(anchor="w", pady=(2, 12))
        body = tk.Frame(self, bg=bg)
        body.pack(fill="x")
        left = card(body, bg=T.CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))
        label(left, _("ЧТО ЭТО ЗА УРОВЕНЬ?"), 9, "bold", fg=T.MUTED, bg=T.CARD).pack(anchor="w", padx=22, pady=(20, 0))
        self.item_lbl = label(left, "", 24, "bold", bg=T.CARD, wraplength=420, justify="left")
        self.item_lbl.pack(anchor="w", padx=22, pady=(6, 10))
        self.fb = label(left, "", 12, "bold", bg=T.CARD, wraplength=420, justify="left")
        self.fb.pack(anchor="w", padx=22)
        self.expl = label(left, "", 11, fg=T.MUTED, bg=T.CARD, wraplength=420, justify="left")
        self.expl.pack(anchor="w", padx=22, pady=(4, 8))
        self.b_next = FlatButton(left, _("Следующий  →"), self.next_item, kind="primary")
        self.stats = label(left, "", 10, fg=T.MUTED, bg=T.CARD)
        self.stats.pack(side="bottom", anchor="w", padx=22, pady=16)

        right = tk.Frame(body, bg=bg)
        right.pack(side="left", fill="y")
        self.btns = {}
        for layer in range(7, 0, -1):
            col = T.LAYER[layer]
            b = FlatButton(right, f"{layer}   {T.layer_name(layer)}", command=lambda l=layer: self.answer(l),
                           bg=T.tint(col, 0.55, T.BG), fg=T.TEXT, anchor="w", width=22, size=11, pady=9)
            b.pack(fill="x", pady=3)
            self.btns[layer] = b
        self.bind("<Destroy>", self._on_destroy)
        self.next_item()

    def _on_destroy(self, e):
        if e.widget is self and self._job:
            self.after_cancel(self._job)

    def next_item(self):
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        if not self.deck:
            self.deck = self.items[:]
            random.shuffle(self.deck)
        self.current = self.deck.pop()
        self.item_lbl.configure(text=_(self.current[0]))
        self.fb.configure(text="")
        self.expl.configure(text="")
        self.answered = False
        self.b_next.pack_forget()
        for layer, b in self.btns.items():
            b.set_colors(bg=T.tint(T.LAYER[layer], 0.55, T.BG), fg=T.TEXT)
        self._stats()

    def _stats(self):
        self.stats.configure(text=_("Верно: {ok} из {n}   ·   Серия: {s}").format(ok=self.score, n=self.total, s=self.streak))

    def answer(self, layer):
        if self.answered:
            return
        self.answered = True
        _name, correct, why = self.current
        self.total += 1
        self.btns[correct].set_colors(bg=T.GOOD, fg=T.ON_ACCENT)
        if layer == correct:
            self.score += 1
            self.streak += 1
            self.fb.configure(text=_("✔  Верно: {n} — {name}").format(n=correct, name=T.layer_name(correct)), fg=T.GOOD)
            self.expl.configure(text=_(why))
            if self.on_solved and self.streak % 5 == 0:
                self.on_solved()
            self._job = self.after(1300, self.next_item)
        else:
            self.streak = 0
            self.btns[layer].set_colors(bg=T.BAD, fg=T.ON_ACCENT)
            self.fb.configure(text=_("✘  Это уровень {n} — {name}").format(n=correct, name=T.layer_name(correct)), fg=T.BAD)
            self.expl.configure(text=_(why))
            self.b_next.pack(anchor="w", padx=22, pady=(4, 8))
        self._stats()
