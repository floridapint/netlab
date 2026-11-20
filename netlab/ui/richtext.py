"""RichText — Text-виджет с мини-разметкой.

Поддерживается:
  # / ## / ###  заголовки        - пункт списка      1. нумерованный пункт
  > подсказка    !> предупреждение    ``` блок кода ```
  |a|b|  таблица (первая строка — шапка, строка из --- пропускается)
  **жирный**  `код`   (внутри строки)
"""
from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk

from .. import theme as T

_INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")
_NUM = re.compile(r"^\d+\.\s")
_SEP = re.compile(r"^:?-{2,}:?$")


class RichText(tk.Frame):
    def __init__(self, master, bg=None, height=12, scroll=True, padx=26, pady=18, size=11, width=60, **kw):
        bg = bg or T.BG
        super().__init__(master, bg=bg, **kw)
        self.bg = bg
        self.size = size
        self.text = tk.Text(self, bg=bg, fg=T.TEXT, relief="flat", bd=0, wrap="word", padx=padx, pady=pady,
                            highlightthickness=0, cursor="arrow", insertwidth=0, height=height, width=width,
                            selectbackground="#1e3a5f", selectforeground=T.TEXT, font=T.F(size),
                            spacing1=2, spacing3=3, takefocus=0)
        if scroll:
            sb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
            self.text.configure(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self._setup_tags()
        self.text.configure(state="disabled")

    def _cfg(self, tag, **opts):
        try:
            self.text.tag_configure(tag, **opts)
        except tk.TclError:  # старые Tk без lmargincolor/rmargincolor
            for k in ("lmargincolor", "rmargincolor"):
                opts.pop(k, None)
            self.text.tag_configure(tag, **opts)

    def _setup_tags(self):
        s = self.size
        self._cfg("h1", font=T.F(s + 9, "bold"), foreground=T.TEXT, spacing1=6, spacing3=10)
        self._cfg("h2", font=T.F(s + 4, "bold"), foreground=T.ACCENT, spacing1=18, spacing3=6)
        self._cfg("h3", font=T.F(s + 1, "bold"), foreground=T.TEXT, spacing1=10, spacing3=3)
        self._cfg("bold", font=T.F(s, "bold"), foreground="#ffffff")
        self._cfg("code", font=T.F(s - 1, mono=True), foreground="#7dd3fc", background=T.CODE_BG)
        self._cfg("codebold", font=T.F(s, "bold", mono=True), foreground="#ffffff", background=T.CODE_BG)
        self._cfg("bullet", lmargin1=18, lmargin2=38)
        self._cfg("codeblock", font=T.F(s - 1, mono=True), foreground="#cbd5e1", background=T.CODE_BG,
                  lmargin1=18, lmargin2=18, rmargin=18, spacing1=0, spacing3=0,
                  lmargincolor=self.bg, rmargincolor=self.bg)
        self._cfg("tip", background="#0f2a3d", lmargin1=18, lmargin2=18, rmargin=18, spacing1=6, spacing3=6,
                  lmargincolor=self.bg)
        self._cfg("warn", background="#33270f", lmargin1=18, lmargin2=18, rmargin=18, spacing1=6, spacing3=6,
                  lmargincolor=self.bg)
        self._cfg("table", font=T.F(s - 1, mono=True), foreground=T.TEXT, lmargin1=18, lmargin2=18,
                  spacing1=1, spacing3=1)
        self._cfg("thead", font=T.F(s - 1, "bold", mono=True), foreground=T.ACCENT, lmargin1=18, lmargin2=18,
                  spacing1=4)
        self._cfg("tline", font=T.F(s - 1, mono=True), foreground=T.DIM, lmargin1=18, spacing1=0, spacing3=0)
        self._cfg("gap", font=T.F(4))
        self._cfg("muted", foreground=T.MUTED)
        self._cfg("good", foreground=T.GOOD)
        self._cfg("bad", foreground=T.BAD)
        self._cfg("warncolor", foreground=T.WARN)
        self.text.tag_raise("bold")
        self.text.tag_raise("code")
        self.text.tag_raise("codebold")

    # ------------------------------------------------------------------
    def _inline(self, line: str, tags=()):
        for part in _INLINE.split(line):
            if not part:
                continue
            if part.startswith("**") and part.endswith("**") and len(part) > 4:
                inner = part[2:-2]
                if len(inner) > 2 and inner.startswith("`") and inner.endswith("`"):
                    self.text.insert("end", f" {inner[1:-1]} ", (*tags, "codebold"))
                else:
                    self.text.insert("end", inner, (*tags, "bold"))
            elif part.startswith("`") and part.endswith("`") and len(part) > 2:
                self.text.insert("end", f" {part[1:-1]} ", (*tags, "code"))
            else:
                self.text.insert("end", part, tags)

    def _table(self, rows):
        cells = []
        for r in rows:
            parts = [c.strip() for c in r.strip().strip("|").split("|")]
            if all(_SEP.match(p) for p in parts if p):
                continue
            cells.append([p.replace("**", "").replace("`", "") for p in parts])
        if not cells:
            return
        ncol = max(len(r) for r in cells)
        for r in cells:
            r += [""] * (ncol - len(r))
        widths = [max(len(r[i]) for r in cells) for i in range(ncol)]
        for idx, r in enumerate(cells):
            line = "  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip()
            self.text.insert("end", line + "\n", "thead" if idx == 0 else "table")
            if idx == 0:
                self.text.insert("end", "─" * (sum(widths) + 2 * (ncol - 1)) + "\n", "tline")

    def render(self, markup: str, append: bool = False):
        t = self.text
        t.configure(state="normal")
        if not append:
            t.delete("1.0", "end")
        lines = markup.strip("\n").split("\n")
        i = 0
        in_code = False
        while i < len(lines):
            raw = lines[i]
            line = raw.rstrip()
            if line.strip().startswith("```"):
                in_code = not in_code
                i += 1
                continue
            if in_code:
                t.insert("end", " " + raw + " \n", "codeblock")
                i += 1
                continue
            s = line.strip()
            if s.startswith("|"):
                block = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    block.append(lines[i])
                    i += 1
                self._table(block)
                continue
            if not s:
                t.insert("end", "\n", "gap")
            elif s.startswith("### "):
                self._inline(s[4:], ("h3",))
                t.insert("end", "\n", "h3")
            elif s.startswith("## "):
                self._inline(s[3:], ("h2",))
                t.insert("end", "\n", "h2")
            elif s.startswith("# "):
                self._inline(s[2:], ("h1",))
                t.insert("end", "\n", "h1")
            elif s.startswith("!>"):
                self._inline("⚠  " + s[2:].strip(), ("warn",))
                t.insert("end", "\n", "warn")
            elif s.startswith(">"):
                self._inline("➜  " + s[1:].strip(), ("tip",))
                t.insert("end", "\n", "tip")
            elif s.startswith("- ") or s.startswith("• "):
                self._inline("•  " + s[2:], ("bullet",))
                t.insert("end", "\n", "bullet")
            elif _NUM.match(s):
                self._inline(s, ("bullet",))
                t.insert("end", "\n", "bullet")
            else:
                self._inline(s)
                t.insert("end", "\n")
            i += 1
        t.configure(state="disabled")

    def set_plain(self, text: str, tag=None):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", text, tag or ())
        self.text.configure(state="disabled")
