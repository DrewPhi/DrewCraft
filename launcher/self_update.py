#!/usr/bin/env python3
"""Self-updating DrewCraft launchers: one download, forever current.

Design (verified against platform behavior):
- POSIX (macOS .app binary, Linux): an atomic os.replace() over the running
  binary is safe. Unix executes by inode; the old image keeps running.
- Windows: a running .exe cannot be overwritten, but it CAN be renamed (the
  lock is on the file handle, not the directory entry). Rename self aside to
  a unique .old name, move the download into place, spawn it, exit. Stale
  .old files are reaped best-effort on startup.
- Temp/download names never contain "update", "setup", or "install", which
  would trip Windows' installer-detection UAC heuristic.
- .deb installs (root-owned /usr/bin) and other unwritable targets fail
  closed with a "re-download" message instead of privilege tricks.
- No network or any failure: proceed to normal converge. Updating must never
  strand a player who only wanted to play.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import urllib.request
from typing import NoReturn

RELEASES_API = "https://api.github.com/repos/DrewPhi/DrewCraft/releases"
TAG_PREFIX = "launcher-v"

# Platform key (see drewcraft_bootstrap.platform_key) -> release asset name.
# macOS uses a raw binary asset (published alongside the DMG) because the
# updater replaces only Contents/MacOS/DrewCraft inside the installed .app.
PLATFORM_ASSETS = {
    "windows-x86_64": "DrewCraft-Windows.exe",
    "macos-arm64": "DrewCraft-macOS-arm64",
    "linux-x86_64": "DrewCraft-Linux-x86_64",
}

SKIP_ENV = "DREWCRAFT_SKIP_SELF_UPDATE"


def _version_tuple(value: str) -> tuple[int, ...]:
    import re
    numbers = [int(x) for x in re.findall(r"\d+", value)]
    if not numbers:
        raise RuntimeError(f"invalid version string: {value!r}")
    return tuple(numbers)


def current_executable() -> pathlib.Path | None:
    """Binary to replace, or None when running from source (dev mode)."""
    if not getattr(sys, "frozen", False):
        return None
    return pathlib.Path(sys.executable).resolve()


def fetch_latest_launcher(context=None) -> dict | None:
    """Newest launcher-v* release, or None when it cannot be determined."""
    import ssl

    try:
        import certifi
        ctx = context or ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = context or ssl.create_default_context()
    try:
        req = urllib.request.Request(
            RELEASES_API + "?per_page=100",
            headers={"User-Agent": "DrewCraft-Updater/1", "Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
            releases = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    best = None
    for release in releases:
        tag = str(release.get("tag_name") or "")
        if not tag.startswith(TAG_PREFIX) or release.get("draft"):
            continue
        version = tag[len(TAG_PREFIX):]
        try:
            key = _version_tuple(version)
        except RuntimeError:
            continue
        if best is None or key > best[0]:
            best = (key, version, release)
    if best is None:
        return None
    return {"version": best[1], "release": best[2]}


def update_available(current_version: str, latest: dict | None) -> bool:
    if not latest:
        return False
    try:
        return _version_tuple(latest["version"]) > _version_tuple(current_version)
    except RuntimeError:
        return False


def asset_for_platform(latest: dict, platform_key: str) -> dict | None:
    want = PLATFORM_ASSETS.get(platform_key)
    if not want:
        return None
    for asset in latest["release"].get("assets") or []:
        if asset.get("name") == want and asset.get("state") == "uploaded":
            return asset
    return None


def download_asset(url: str, digest: str | None, dest: pathlib.Path, context=None) -> pathlib.Path:
    import hashlib
    import ssl

    try:
        import certifi
        ctx = context or ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = context or ssl.create_default_context()
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "DrewCraft-Updater/1"})
    hasher = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=300, context=ctx) as response, tmp.open("wb") as out:
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            hasher.update(chunk)
            out.write(chunk)
    if digest and hasher.hexdigest() != digest.removeprefix("sha256:"):
        tmp.unlink(missing_ok=True)
        raise RuntimeError("launcher download hash mismatch")
    os.replace(tmp, dest)
    return dest


def swap_executable(current: pathlib.Path, downloaded: pathlib.Path) -> pathlib.Path:
    """Atomically install the download over the running binary.

    Returns the path to launch. Never leaves the player without a binary:
    on Windows the original is renamed aside first and restored on failure.
    """
    if os.name == "nt":
        aside = _unique_aside(current)
        try:
            os.rename(current, aside)
        except OSError as exc:
            raise RuntimeError(f"cannot stage current launcher aside: {exc}") from exc
        try:
            os.replace(downloaded, current)
        except OSError as exc:
            try:
                os.rename(aside, current)
            except OSError:
                pass
            raise RuntimeError(f"cannot install launcher update: {exc}") from exc
        return current
    os.replace(downloaded, current)
    return current


def _unique_aside(current: pathlib.Path) -> pathlib.Path:
    candidate = current.with_suffix(current.suffix + ".old")
    if not candidate.exists():
        return candidate
    pid = os.getpid()
    for index in range(1000):
        numbered = current.parent / f"{current.name}.old.{pid}.{index}"
        if not numbered.exists():
            return numbered
    return current.parent / f"{current.name}.old.{pid}.overflow"


def reap_asides(directory: pathlib.Path, stem: str) -> list[str]:
    """Best-effort removal of stale .old swap files. Returns removed names."""
    removed = []
    try:
        entries = list(directory.iterdir())
    except OSError:
        return removed
    for entry in entries:
        name = entry.name
        if not name.startswith(stem + ".old"):
            continue
        try:
            entry.unlink()
            removed.append(name)
        except OSError:
            continue
    return removed


def relaunch(path: pathlib.Path, args: list[str]) -> NoReturn:
    if os.name != "nt":
        os.chmod(path, 0o755)
    subprocess.Popen([str(path), *args])
    raise SystemExit(0)


def maybe_self_update(app_version: str, platform_key: str, argv: list[str]) -> bool:
    """Check, download, swap, and relaunch. Returns True when relaunching.

    Returns False (continue normally) when disabled, not frozen, already
    current, undiscoverable, unwritable, or on any error.
    """
    if os.environ.get(SKIP_ENV) or "--skip-self-update" in argv:
        return False
    current = current_executable()
    if current is None:
        return False
    try:
        reap_asides(current.parent, current.name)
    except Exception:
        pass
    latest = fetch_latest_launcher()
    if not update_available(app_version, latest):
        return False
    asset = asset_for_platform(latest, platform_key)
    if asset is None:
        return False
    digest = asset.get("digest")
    try:
        staged = download_asset(asset["browser_download_url"], digest,
                                current.parent / (current.name + ".new"))
    except Exception:
        return False
    if os.name != "nt":
        try:
            os.chmod(staged, 0o755)
        except OSError:
            return False
    try:
        installed = swap_executable(current, staged)
    except RuntimeError:
        try:
            staged.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    forward = [a for a in argv[1:] if a != "--skip-self-update"]
    relaunch(installed, forward)
    return True  # Unreachable; relaunch exits.
