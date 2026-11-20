"""Главное окно NetLab: боковое меню, страницы и выбор языка."""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from . import __version__, i18n, theme as T
from .i18n import _
from .lessons import LESSONS
from .progress import Progress
from .ui.widgets import Segmented, label


class NavItem(tk.Frame):
    def __init__(self, master, title, subtitle, color, command):
        super().__init__(master, bg=T.SIDEBAR, cursor="hand2")
        self.color = color
        self.command = command
        self.selected = False
        self.stripe = tk.Frame(self, bg=T.SIDEBAR, width=4)
        self.stripe.pack(side="left", fill="y")
        box = tk.Frame(self, bg=T.SIDEBAR)
        box.pack(side="left", fill="x", padx=(14, 10), pady=7)
        self.t = tk.Label(box, text=title, font=T.F(11, "bold"), fg=T.TEXT, bg=T.SIDEBAR, anchor="w")
        self.t.pack(anchor="w")
        self.s = tk.Label(box, text=subtitle, font=T.F(8), fg=T.DIM, bg=T.SIDEBAR, anchor="w")
        if subtitle:
            self.s.pack(anchor="w")
        self.parts = [self, box, self.t, self.s]
        for w in self.parts:
            w.bind("<Button-1>", lambda _e: self.command())
            w.bind("<Enter>", lambda _e: self._paint(hover=True))
            w.bind("<Leave>", lambda _e: self._paint())

    def _paint(self, hover=False):
        bg = T.PANEL2 if self.selected else (T.PANEL if hover else T.SIDEBAR)
        for w in self.parts:
            w.configure(bg=bg)
        self.stripe.configure(bg=self.color if self.selected else bg)
        self.t.configure(fg=T.TEXT if self.selected or hover else T.MUTED)

    def set_selected(self, flag):
        self.selected = flag
        self._paint()


class App(tk.Tk):
    def __init__(self, progress: Progress | None = None, lang: str | None = None):
        super().__init__()
        T.init(self)
        self.progress = progress or Progress.load()
        i18n.set_lang(lang or self.progress.data.get("lang") or i18n.detect())
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(1360, sw - 40), min(900, sh - 80)
        self.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 3)}")
        self.minsize(1100, 680)
        self._set_icon()
        self.report_callback_exception = self._on_error
        self.pages: dict = {}
        self.nav: dict = {}
        self.current = None
        self.sidebar = None
        self.content = None
        self._build_ui()
        self.show("home")

    # ------------------------------------------------------------------ сборка интерфейса
    def _build_ui(self):
        self.title(_("NetLab {v} — интерактивная лаборатория сетей").format(v=__version__))
        self.sidebar = tk.Frame(self, bg=T.SIDEBAR, width=232)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.content = tk.Frame(self, bg=T.BG)
        self.content.pack(side="left", fill="both", expand=True)
        self._build_sidebar()

    def set_language(self, code):
        if code == i18n.get_lang():
            return
        i18n.set_lang(code)
        self.progress.data["lang"] = code
        self.progress.save()
        current = self.current or "home"
        for page in list(self.pages.values()):
            page.destroy()
        self.pages.clear()
        self.nav.clear()
        self.current = None
        self.sidebar.destroy()
        self.content.destroy()
        self._build_ui()
        self.show(current)

    def _set_icon(self):
        try:
            img = tk.PhotoImage(width=32, height=32)
            img.put(T.BG, to=(0, 0, 32, 32))
            for i, col in enumerate((T.LAYER[7], T.LAYER[4], T.LAYER[3], T.LAYER[1])):
                img.put(col, to=(4, 4 + i * 6, 28, 8 + i * 6))
            self.iconphoto(True, img)
            self._icon = img
        except tk.TclError:
            pass

    def _build_sidebar(self):
        sb = self.sidebar
        logo = tk.Frame(sb, bg=T.SIDEBAR)
        logo.pack(fill="x", padx=20, pady=(22, 18))
        row = tk.Frame(logo, bg=T.SIDEBAR)
        row.pack(anchor="w")
        for col in (T.LAYER[7], T.LAYER[4], T.LAYER[3], T.LAYER[1]):
            tk.Frame(row, bg=col, width=6, height=22).pack(side="left", padx=1)
        label(row, "  NetLab", 19, "bold", bg=T.SIDEBAR).pack(side="left")
        label(logo, _("лаборатория сетевых протоколов"), 9, fg=T.DIM, bg=T.SIDEBAR, wraplength=190,
              justify="left").pack(anchor="w", pady=(4, 0))

        self._add_nav("home", _("Главная"), _("обзор и прогресс"), T.ACCENT)
        label(sb, _("УРОКИ"), 8, "bold", fg=T.DIM, bg=T.SIDEBAR).pack(anchor="w", padx=22, pady=(14, 4))
        for lesson in LESSONS:
            self._add_nav(lesson.key, f"{lesson.number}.  {_(lesson.short)}", "", lesson.color)
        label(sb, _("ПРОВЕРКА И СПРАВКА"), 8, "bold", fg=T.DIM, bg=T.SIDEBAR).pack(anchor="w", padx=22, pady=(14, 4))
        self._add_nav("exam", _("★  Экзамен"), _("все темы вперемешку"), T.WARN)
        self._add_nav("ref", _("☰  Справочник"), _("порты, команды, шпаргалка"), T.ACCENT2)

        bottom = tk.Frame(sb, bg=T.SIDEBAR)
        bottom.pack(side="bottom", fill="x", padx=22, pady=14)
        label(bottom, _("ЯЗЫК"), 8, "bold", fg=T.DIM, bg=T.SIDEBAR).pack(anchor="w")
        codes = list(i18n.LANGS)
        Segmented(bottom, [i18n.SHORT[c] for c in codes], index=codes.index(i18n.get_lang()), size=9, bg=T.SIDEBAR,
                  command=lambda i: self.after_idle(self.set_language, codes[i])).pack(anchor="w", pady=(4, 10))
        label(bottom, f"v{__version__} · Python {sys.version_info.major}.{sys.version_info.minor} · tkinter", 8,
              fg=T.DIM, bg=T.SIDEBAR).pack(anchor="w")

    def _add_nav(self, key, title, subtitle, color):
        item = NavItem(self.sidebar, title, subtitle, color, lambda: self.show(key))
        item.pack(fill="x")
        self.nav[key] = item

    def _make_page(self, key):
        from .lessons import BY_KEY
        from .pages.exam import ExamPage
        from .pages.home import HomePage
        from .pages.lesson import LessonPage
        from .pages.reference import ReferencePage

        if key == "home":
            return HomePage(self.content, self)
        if key == "exam":
            return ExamPage(self.content, self)
        if key == "ref":
            return ReferencePage(self.content, self)
        return LessonPage(self.content, self, BY_KEY[key])

    def show(self, key):
        if key not in self.pages:
            self.pages[key] = self._make_page(key)
        if self.current and self.current != key:
            self.pages[self.current].pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        self.current = key
        for k, item in self.nav.items():
            item.set_selected(k == key)
        page = self.pages[key]
        if hasattr(page, "select_tab") and not page.built:
            page.select_tab(0)
        return page

    def _on_error(self, exc, val, tb):
        print("".join(traceback.format_exception(exc, val, tb)), file=sys.stderr)
        try:
            messagebox.showerror(_("Ошибка"), _("Что-то пошло не так:\n\n{e}\n\nПодробности выведены в консоль.").format(e=val),
                                 parent=self)
        except tk.TclError:
            pass


def selftest(langs=("ru", "en", "uk")) -> int:
    """Opens every page, tab and tool and plays every animation in each language. Exit code 0 = OK."""
    from .ui.animation import AnimationPlayer

    errors = []
    for lang in langs:
        tmp = Path(tempfile.mkdtemp(prefix="netlab-selftest-"))
        app = App(Progress(tmp / "progress.json"), lang=lang)
        app.report_callback_exception = lambda e, v, tb: errors.append("".join(traceback.format_exception(e, v, tb)))
        try:
            for key in ["home", "exam", "ref"] + [lsn.key for lsn in LESSONS]:
                page = app.show(key)
                app.update()
                if hasattr(page, "select_tab"):
                    for i in range(5):
                        page.select_tab(i)
                        app.update()
            for lsn in LESSONS:
                stack = [app.pages[lsn.key]]
                while stack:
                    w = stack.pop()
                    stack.extend(w.winfo_children())
                    if isinstance(w, AnimationPlayer):
                        w.run_all_instantly()
                        app.update()
                    if w.__class__.__name__ == "SwitchPanel":
                        for i in range(len(w.items)):
                            w.show(i)
                            app.update()
                            stack.extend(w.frames[i].winfo_children())
            app.show("exam")._start()
            app.update()
            other = "en" if lang != "en" else "uk"
            app.set_language(other)
            app.update()
            print(f"selftest [{lang}]: pages OK, errors so far: {len(errors)}")
        except Exception:  # noqa: BLE001
            errors.append(traceback.format_exc())
        finally:
            for page in app.pages.values():
                page.destroy()
            app.destroy()
    if i18n.missing:
        print(f"selftest: {len(i18n.missing)} untranslated runtime strings:", file=sys.stderr)
        for s in sorted(i18n.missing)[:40]:
            print("   ", repr(s[:90]), file=sys.stderr)
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors or i18n.missing else 0


def main():
    parser = argparse.ArgumentParser(description="NetLab - interactive networking lab (OSI, TCP/IP, IP, UDP, TCP, TLS)")
    parser.add_argument("--lang", choices=list(i18n.LANGS), help="interface language: ru, en, uk")
    parser.add_argument("--page", help="open a page: home, osi, tcpip, ip, udp, tcp, tls, exam, ref")
    parser.add_argument("--tab", type=int, default=0, help="lesson tab (0-4)")
    parser.add_argument("--scenario", type=int, default=0, help="animation index on the Animations tab")
    parser.add_argument("--step", type=int, default=0, help="jump the animation to step N")
    parser.add_argument("--selftest", action="store_true", help="open every screen and play every animation, then exit")
    args = parser.parse_args()
    if args.selftest:
        sys.exit(selftest((args.lang,) if args.lang else ("ru", "en", "uk")))
    if os.name == "nt":
        try:  # своя иконка в панели задач, а не иконка Python
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("netlab.app")
        except (AttributeError, OSError):
            pass
    app = App(lang=args.lang)
    if args.page:
        page = app.show(args.page)
        if hasattr(page, "select_tab"):
            page.select_tab(args.tab)
            player = getattr(page, "player", None)
            if player and (args.scenario or args.step):
                player.load(args.scenario)
                player._rebuild(min(args.step, len(player.steps)))
    app.mainloop()


if __name__ == "__main__":
    main()
