"""Localization checks: every translatable string has EN and UK translations,
and no Russian literal is left outside _() / N_()."""
import ast
import unittest
from pathlib import Path

from netlab.i18n import LANGS
from netlab.locales import TR, content_en, content_uk
from netlab.core.questions import QUESTIONS

ROOT = Path(__file__).resolve().parent.parent / "netlab"
CYR = set("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюяІіЇїЄєҐґ")
# Large Russian blocks that are translated as whole documents in locales/content_*.py
SKIP_ASSIGN = {"THEORY", "COMPARE", "QUESTIONS", "YES", "NO"}  # YES/NO — accepted answers, not UI text
SKIP_FILES = {"i18n.py"}


def has_cyr(s):
    return any(ch in CYR for ch in s)


def scan():
    keys, loose = {}, []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("locales/") or path.name in SKIP_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        ok_ids = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    ok_ids.add(id(first.value))
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in SKIP_ASSIGN for t in node.targets):
                ok_ids.update(id(n) for n in ast.walk(node))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("_", "N_"):
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    keys.setdefault(node.args[0].value, f"{rel}:{node.lineno}")
                    ok_ids.add(id(node.args[0]))
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                parts = "".join(v.value for v in node.values if isinstance(v, ast.Constant))
                if has_cyr(parts) and id(node) not in ok_ids:
                    loose.append(f"{rel}:{node.lineno}  f-string: {parts[:60]!r}")
                ok_ids.update(id(v) for v in node.values)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and has_cyr(node.value) \
                    and len(node.value) > 1 and id(node) not in ok_ids:
                loose.append(f"{rel}:{node.lineno}  {node.value[:60]!r}")
    return keys, loose


class TestI18n(unittest.TestCase):
    def test_no_untranslated_literals(self):
        _keys, loose = scan()
        self.assertEqual(loose, [], "Russian literals outside _():\n" + "\n".join(loose))

    def test_all_keys_translated(self):
        keys, _loose = scan()
        missing = [f"{where}  {k[:70]!r}" for k, where in keys.items()
                   if k not in TR or not TR[k][0] or not TR[k][1]]
        self.assertEqual(missing, [], "No translation for:\n" + "\n".join(sorted(missing)))

    def test_placeholders_match(self):
        import string
        fmt = string.Formatter()
        bad = []
        for ru, (en, uk) in TR.items():
            names = {f for _, f, _, _ in fmt.parse(ru) if f}
            for tr in (en, uk):
                try:
                    if {f for _, f, _, _ in fmt.parse(tr) if f} != names:
                        bad.append(ru[:60])
                except ValueError:
                    bad.append(ru[:60])
        self.assertEqual(bad, [])

    def test_translations_are_not_russian(self):
        bad = [ru[:50] for ru, (en, _uk) in TR.items() if has_cyr(en)]
        self.assertEqual(bad, [], "English translations with Cyrillic")

    def test_content_modules(self):
        for mod in (content_en, content_uk):
            self.assertEqual(set(mod.THEORY), {"osi", "tcpip", "ip", "udp", "tcp", "tls"})
            self.assertTrue(mod.CHEAT)
            self.assertEqual(set(mod.QUESTIONS), set(QUESTIONS))
            for topic, qs in QUESTIONS.items():
                self.assertEqual(len(mod.QUESTIONS[topic]), len(qs), (mod.__name__, topic))
                for q in mod.QUESTIONS[topic]:
                    self.assertEqual(len(q["options"]), 4)
                    self.assertEqual(len(set(q["options"])), 4, q["q"])

    def test_langs(self):
        self.assertEqual(set(LANGS), {"ru", "en", "uk"})


if __name__ == "__main__":
    unittest.main()
