#!/usr/bin/env python3
"""Double-click entrypoint for the DrewCraft friend installer/launcher."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

from drewcraft_bootstrap import converge, default_app_dir, launch

LIVE_URL = "https://drewphi.github.io/DrewCraft/live.json"


def _needs_login(state: dict) -> bool:
    accounts = pathlib.Path(state["prismRoot"]) / "accounts.json"
    if not accounts.is_file():
        return True
    try:
        payload = json.loads(accounts.read_text("utf-8"))
    except Exception:
        return True
    accounts_list = payload.get("accounts")
    return not isinstance(accounts_list, list) or not accounts_list


def _message(title: str, text: str, *, error: bool = False) -> None:
    try:
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        (messagebox.showerror if error else messagebox.showinfo)(title, text)
        root.destroy()
    except Exception:
        print(f"{title}: {text}", file=sys.stderr if error else sys.stdout)


def main() -> int:
    app_dir = default_app_dir()
    state = converge(LIVE_URL, app_dir)
    if _needs_login(state):
        _message(
            "DrewCraft",
            "DrewCraft is installed and up to date. Prism Launcher will open for the one-time Microsoft sign-in. After signing in, close Prism and open DrewCraft again.",
        )
        prism = state.get("prismExecutable")
        if not prism:
            raise RuntimeError("Prism runtime is not configured")
        subprocess.Popen([prism, "--dir", state["prismRoot"]])
        return 0
    return launch(app_dir)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        _message("DrewCraft could not start", str(exc), error=True)
        raise SystemExit(1)
