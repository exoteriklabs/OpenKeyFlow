"""Convenience launcher for OpenKeyFlow."""
from __future__ import annotations

import importlib.util
import sys


def _ensure_dependencies() -> None:
    missing = [
        name
        for name in ("PyQt5", "keyboard", "pyperclip")
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        joined = ", ".join(sorted(set(missing)))
        command = f"{sys.executable} -m pip install -r requirements.txt"
        sys.stderr.write(
            "Required packages missing: "
            f"{joined}.\n"
            "Install them for this interpreter with:\n"
            f"  {command}\n"
        )
        sys.exit(1)


def main() -> None:
    _ensure_dependencies()
    from app.main import main as app_main

    app_main()
from app.main import main


if __name__ == "__main__":
    main()
