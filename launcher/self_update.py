#!/usr/bin/env python3
"""Self-updating DrewCraft launchers: one download, forever current.

Design:
- Windows: a running .exe cannot be overwritten, but it can be renamed. The
  updater renames the current image aside, atomically installs the new image,
  relaunches it, and reaps stale .old files on later starts.
- macOS: the installed app's executable is replaced atomically with the raw
  arm64 executable published beside the DMG.
- Linux: a writable standalone executable updates in place. A root-owned .deb
  install delegates future updates to a per-user executable under XDG data, so
  the user never needs sudo or another website download.
- Every start checks both launcher version and the published SHA-256 digest.
  This means a rebuilt launcher under the same version tag still propagates.
- Any network/update failure fails open into normal pack convergence so an
  updater outage never prevents someone from playing.
"""
from __future__ import annotations

import hashlib
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
# macOS and Linux publish raw updater-consumed executables alongside their
# friend-facing DMG/.deb packages.
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


def sha256_file(path: pathlib.Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _asset_digest(asset: dict | None) -> str | None:
    if not asset:
        return None
    digest = str(asset.get("digest") or "")
    if not digest.startswith("sha256:"):
        return None
    value = digest.removeprefix("sha256:").lower()
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        return None
    return value


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


def update_available(
    current_version: str,
    latest: dict | None,
    asset: dict | None = None,
    current: pathlib.Path | None = None,
) -> bool:
    """Return whether the running launcher should be replaced.

    A newer semantic version always wins. For equal versions, compare the
    release asset digest against the running binary so CI can safely clobber a
    release asset and still propagate an urgent launcher-only fix.
    """
    if not latest:
        return False
    try:
        latest_version = _version_tuple(latest["version"])
        running_version = _version_tuple(current_version)
    except (KeyError, RuntimeError):
        return False
    if latest_version > running_version:
        return True
    if latest_version < running_version:
        return False
    expected = _asset_digest(asset)
    if expected is None or current is None:
        return False
    try:
        return sha256_file(current) != expected
    except OSError:
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
    expected = None
    if digest:
        value = str(digest)
        expected = value.removeprefix("sha256:") if value.startswith("sha256:") else value
    if expected and hasher.hexdigest() != expected:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("launcher download hash mismatch")
    os.replace(tmp, dest)
    return dest


def swap_executable(current: pathlib.Path, downloaded: pathlib.Path) -> pathlib.Path:
    """Atomically install the download over the target executable."""
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


def update_target(current: pathlib.Path, platform_key: str) -> pathlib.Path:
    """Choose an updateable target without requiring privilege escalation."""
    if platform_key != "linux-x86_64" or os.access(current.parent, os.W_OK):
        return current
    xdg = os.environ.get("XDG_DATA_HOME")
    base = pathlib.Path(xdg).expanduser() if xdg else pathlib.Path.home() / ".local" / "share"
    return base / "DrewCraft" / "launcher" / "DrewCraft-Linux-x86_64"


def _matches_asset(path: pathlib.Path, asset: dict) -> bool:
    expected = _asset_digest(asset)
    if expected is None or not path.is_file():
        return False
    try:
        return sha256_file(path) == expected
    except OSError:
        return False


def relaunch(path: pathlib.Path, args: list[str]) -> NoReturn:
    if os.name != "nt":
        os.chmod(path, 0o755)
    subprocess.Popen([str(path), *args])
    raise SystemExit(0)


def maybe_self_update(app_version: str, platform_key: str, argv: list[str]) -> bool:
    """Check, download, swap, and relaunch before normal pack convergence."""
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
    if latest is None:
        return False
    asset = asset_for_platform(latest, platform_key)
    if asset is None:
        return False
    if not update_available(app_version, latest, asset, current):
        return False

    target = update_target(current, platform_key)
    forward = [a for a in argv[1:] if a != "--skip-self-update"]

    # A root-owned Linux package may repeatedly enter through /usr/bin. If the
    # already-downloaded user-local launcher matches the current release, just
    # hand off to it instead of downloading again.
    if target != current and _matches_asset(target, asset):
        relaunch(target, forward)

    digest = asset.get("digest")
    try:
        staged = download_asset(
            asset["browser_download_url"], digest, target.parent / (target.name + ".new")
        )
    except Exception:
        return False
    if os.name != "nt":
        try:
            os.chmod(staged, 0o755)
        except OSError:
            staged.unlink(missing_ok=True)
            return False
    try:
        if target.exists():
            installed = swap_executable(target, staged)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged, target)
            installed = target
    except (OSError, RuntimeError):
        try:
            staged.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    relaunch(installed, forward)
    return True  # Unreachable; relaunch exits.
