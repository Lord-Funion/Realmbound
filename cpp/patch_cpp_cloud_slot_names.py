#!/usr/bin/env python3
"""Keep C++ cloud saves out of the browser autosave slot."""

from __future__ import annotations

import sys
from pathlib import Path


def require_replace(text: str, old: str, new: str) -> str:
    if old not in text:
        raise SystemExit(f"slot-name patch marker not found: {old}")
    return text.replace(old, new)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_cpp_cloud_slot_names.py <generated.cpp>")

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    text = require_replace(text, 'return safe.empty() ? "autosave" : safe.substr(0, 64);', 'return safe.empty() ? "cpp_autosave" : safe.substr(0, 64);')
    text = require_replace(text, 'bool cloud_upload_state(const State& state, const std::string& default_slot = "autosave", bool quiet = false)', 'bool cloud_upload_state(const State& state, const std::string& default_slot = "cpp_autosave", bool quiet = false)')
    text = require_replace(text, 'Cloud save slot to download [autosave]: ', 'Cloud save slot to download [cpp_autosave]: ')
    text = require_replace(text, 'cloud_upload_state(state, "autosave", true)', 'cloud_upload_state(state, "cpp_autosave", true)')
    path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
