#!/usr/bin/env python3
"""Double-click entrypoint for the DrewCraft friend installer/launcher."""
from __future__ import annotations

import contextlib
import json
import os
import pathlib
import queue
import subprocess
import sys
import threading

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


@contextlib.contextmanager
def _single_instance(app_dir: pathlib.Path):
    app_dir.mkdir(parents=True, exist_ok=True)
    lock = app_dir / "launcher.lock"
    for _ in range(2):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w", encoding="ascii") as fh:
                fh.write(str(os.getpid()))
            break
        except FileExistsError:
            try:
                pid = int(lock.read_text("ascii").strip())
                os.kill(pid, 0)
            except (OSError, ValueError):
                lock.unlink(missing_ok=True)
                continue
            raise RuntimeError("DrewCraft is already installing or running. Check the existing window.")
    else:
        raise RuntimeError("Could not acquire the DrewCraft launcher lock")
    try:
        yield
    finally:
        try:
            if lock.read_text("ascii").strip() == str(os.getpid()):
                lock.unlink()
        except OSError:
            pass


def _format_bytes(value: float) -> str:
    return f"{value / (1024 * 1024):.1f} MB"


def _terminal_progress(event: dict) -> None:
    if event["phase"] == "download":
        total = event.get("total", 0)
        amount = _format_bytes(event["downloaded"])
        suffix = f" / {_format_bytes(total)}" if total else ""
        eta = event.get("etaSeconds", 0)
        print(f"Downloading {event['label']}: {amount}{suffix} · ETA {eta:.0f}s", flush=True)
    elif event["phase"] in ("status", "file", "complete"):
        print(event["label"], flush=True)


def _converge_with_progress(live_url: str, app_dir: pathlib.Path) -> dict:
    try:
        import tkinter
        from tkinter import ttk
        root = tkinter.Tk()
    except Exception:
        return converge(live_url, app_dir, progress=_terminal_progress)

    root.title("DrewCraft")
    root.geometry("520x180")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)
    title = ttk.Label(frame, text="Preparing DrewCraft", font=("TkDefaultFont", 15, "bold"))
    title.pack(anchor="w")
    detail = ttk.Label(frame, text="Checking for updates", wraplength=480)
    detail.pack(anchor="w", pady=(12, 8))
    bar = ttk.Progressbar(frame, mode="indeterminate", length=480)
    bar.pack(fill="x")
    stats = ttk.Label(frame, text="")
    stats.pack(anchor="w", pady=(8, 0))
    bar.start(12)

    events: queue.Queue = queue.Queue()
    result: dict = {}

    def worker():
        try:
            result["state"] = converge(live_url, app_dir, progress=events.put)
        except Exception as exc:
            result["error"] = exc
        finally:
            events.put({"phase": "worker_done", "label": "done"})

    threading.Thread(target=worker, daemon=True).start()

    def update():
        done = False
        while True:
            try:
                event = events.get_nowait()
            except queue.Empty:
                break
            _terminal_progress(event) if event["phase"] != "worker_done" else None
            phase = event["phase"]
            if phase == "download":
                total = event.get("total", 0)
                if total:
                    bar.stop()
                    bar.configure(mode="determinate", maximum=total, value=event["downloaded"])
                detail.configure(text=event["label"])
                eta = event.get("etaSeconds", 0)
                stats.configure(text=f"{_format_bytes(event['downloaded'])} / {_format_bytes(total)} · about {eta:.0f}s remaining")
            elif phase == "file":
                detail.configure(text=event["label"])
                stats.configure(text=f"File {event['fileIndex']} of {event['fileCount']}")
            elif phase in ("status", "complete"):
                detail.configure(text=event["label"])
            elif phase == "worker_done":
                done = True
        if done:
            root.destroy()
        else:
            root.after(100, update)

    root.after(100, update)
    root.mainloop()
    if "error" in result:
        raise result["error"]
    return result["state"]


def main() -> int:
    app_dir = default_app_dir()
    with _single_instance(app_dir):
        state = _converge_with_progress(LIVE_URL, app_dir)
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
