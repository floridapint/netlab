"""Translations. TR maps a Russian source string to (English, Ukrainian)."""
from . import strings_data, strings_lessons, strings_ui

TR: dict = {}
for _mod in (strings_ui, strings_data, strings_lessons):
    TR.update(_mod.TR)
