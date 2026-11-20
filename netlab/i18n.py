"""Localization. Source strings are Russian; translations live in netlab/locales.

_("текст")   -> translated string for the current language (falls back to the source)
N_("текст")  -> marks a string for translation without translating it (for module-level data)
content(kind, key, default) -> large per-language blocks (theory, cheat sheet, question banks)
"""
from __future__ import annotations

import importlib
import locale
import os
import re

LANGS = {"ru": "Русский", "en": "English", "uk": "Українська"}
SHORT = {"ru": "RU", "en": "EN", "uk": "UK"}
_IDX = {"en": 0, "uk": 1}
_CYR = re.compile("[А-Яа-яЁёІіЇїЄєҐґ]")

_lang = "ru"
_tr: dict | None = None
missing: set = set()


def N_(s: str) -> str:
    return s


def _table() -> dict:
    global _tr
    if _tr is None:
        from .locales import TR
        _tr = TR
    return _tr


def set_lang(code: str):
    global _lang
    _lang = code if code in LANGS else "ru"


def get_lang() -> str:
    return _lang


def _(s: str) -> str:
    if _lang == "ru" or not s:
        return s
    entry = _table().get(s)
    if entry is None:
        if _CYR.search(s):
            missing.add(s)
        return s
    return entry[_IDX[_lang]] or s


def content(kind: str, key=None, default=None):
    """Per-language content module netlab/locales/content_<lang>.py (THEORY, CHEAT, QUESTIONS)."""
    if _lang == "ru":
        return default
    mod = importlib.import_module(f"netlab.locales.content_{_lang}")
    value = getattr(mod, kind)
    return value if key is None else value.get(key, default)


def detect() -> str:
    try:
        import ctypes
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
        return {0x19: "ru", 0x22: "uk"}.get(lid, "en")
    except (AttributeError, OSError):
        pass
    loc = (locale.getlocale()[0] or os.environ.get("LANG", "")).lower()
    if loc.startswith(("ru", "russian")):
        return "ru"
    if loc.startswith(("uk", "ukrainian")):
        return "uk"
    return "en"
