#!/usr/bin/env python3
"""DrewCraft friend-facing bootstrap/update/repair launcher.

Prism remains the Minecraft authentication/launch engine. This bootstrapper owns
only DrewCraft's managed application directory and release convergence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile

APP_VERSION = "0.1.6"
PRESERVED_USER_PATHS = (
    "screenshots",
    "resourcepacks",
    "shaderpacks",
    "saves",
    "options.txt",
    # Terrain Diffusion downloads multi-gigabyte model assets during mod
    # construction. They are runtime cache data, not pack-managed content, and
    # must survive the launcher's versioned-instance convergence.
    "terrain-diffusion-models",
)
HARDLINK_PRESERVED_PATHS = frozenset(("terrain-diffusion-models",))


def _replace_path(src: pathlib.Path, dest: pathlib.Path, attempts: int = 5) -> None:
    # Windows transient locks (AV/indexer) can hold newly copied files briefly,
    # making os.replace fail with WinError 32. Retry briefly before giving up.
    last: OSError | None = None
    for attempt in range(attempts):
        try:
            os.replace(src, dest)
            return
        except OSError as exc:
            last = exc
            if attempt < attempts - 1:
                time.sleep(0.2 * (attempt + 1))
    assert last is not None
    raise last


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _https_context() -> "ssl.SSLContext":
    # macOS-bundled Python (and PyInstaller apps) cannot see the system
    # keychain, so bare urlopen() fails there with CERTIFICATE_VERIFY_FAILED
    # on the very first https call. Prefer the certifi bundle when present
    # (CI bundles it into all three OS launchers); otherwise system default.
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def fetch_bytes(url: str, progress=None, label: str = "download") -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"DrewCraft-Launcher/{APP_VERSION}"})
    with urllib.request.urlopen(req, timeout=120, context=_https_context()) as response:
        total = int(response.headers.get("Content-Length", "0") or 0)
        started = time.monotonic()
        downloaded = 0
        payload = bytearray()
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            payload.extend(chunk)
            downloaded += len(chunk)
            elapsed = max(time.monotonic() - started, 0.001)
            rate = downloaded / elapsed
            eta = (total - downloaded) / rate if total > downloaded and rate > 0 else 0.0
            if progress:
                progress({
                    "phase": "download",
                    "label": label,
                    "downloaded": downloaded,
                    "total": total,
                    "bytesPerSecond": rate,
                    "etaSeconds": eta,
                })
        return bytes(payload)


def fetch_json(url: str) -> dict:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def platform_key() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows" and machine in ("amd64", "x86_64"):
        return "windows-x86_64"
    if system == "darwin" and machine in ("arm64", "aarch64"):
        return "macos-arm64"
    if system == "linux" and machine in ("amd64", "x86_64"):
        return "linux-x86_64"
    raise RuntimeError(f"Unsupported DrewCraft launcher platform: {system}/{machine}")


def default_app_dir() -> pathlib.Path:
    if platform.system() == "Windows":
        return pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home())) / "DrewCraft"
    if platform.system() == "Darwin":
        return pathlib.Path.home() / "Library" / "Application Support" / "DrewCraft"
    return pathlib.Path.home() / ".local" / "share" / "DrewCraft"


def _safe_rel(value: str) -> pathlib.PurePosixPath:
    p = pathlib.PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or "." in p.parts or not p.parts:
        raise RuntimeError(f"unsafe managed path: {value}")
    return p


def _version_tuple(value: str) -> tuple[int, ...]:
    numbers = [int(x) for x in re.findall(r"\d+", value)]
    if not numbers:
        raise RuntimeError(f"invalid version string: {value!r}")
    return tuple(numbers)


def validate_manifest(manifest: dict) -> None:
    if manifest.get("schemaVersion") != 1:
        raise RuntimeError("Unsupported DrewCraft release manifest")
    if manifest.get("java", {}).get("major") != 21:
        raise RuntimeError("DrewCraft release does not declare Java 21")
    if not manifest.get("packVersion") or not isinstance(manifest.get("files"), list):
        raise RuntimeError("Malformed DrewCraft release manifest")
    loader = manifest.get("loader", {})
    if loader.get("id") != "neoforge" or not loader.get("version"):
        raise RuntimeError("DrewCraft V1 requires an exact NeoForge loader version")
    if not manifest.get("minecraftVersion"):
        raise RuntimeError("DrewCraft release is missing minecraftVersion")
    minimum = manifest.get("minimumLauncherVersion", "0")
    if _version_tuple(APP_VERSION) < _version_tuple(minimum):
        raise RuntimeError(
            f"This DrewCraft launcher is too old ({APP_VERSION}); release requires {minimum} or newer"
        )
    seen_paths = set()
    for entry in manifest["files"]:
        path = str(_safe_rel(entry["path"]))
        if path in seen_paths:
            raise RuntimeError(f"duplicate managed path in release manifest: {path}")
        seen_paths.add(path)
        if entry["side"] not in ("common", "client", "server"):
            raise RuntimeError("Malformed release side")
        if not isinstance(entry.get("size"), int) or entry["size"] < 0:
            raise RuntimeError(f"invalid release size for {path}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", ""))):
            raise RuntimeError(f"invalid release SHA-256 for {path}")
        if not str(entry.get("url", "")).startswith(("https://", "file://")):
            raise RuntimeError(f"unsupported release URL for {path}")


def atomic_json(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, sort_keys=True, separators=(",", ":"))
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def verify_entry(path: pathlib.Path, entry: dict) -> bool:
    return path.is_file() and path.stat().st_size == entry["size"] and sha256_file(path) == entry["sha256"]


def selected_files(manifest: dict) -> list[dict]:
    return [e for e in manifest["files"] if e["side"] in ("common", "client")]


def download_verified(url: str, expected_sha: str, destination: pathlib.Path,
                      expected_size: int | None = None, progress=None, label: str | None = None,
                      cancelled=None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    existing = partial.stat().st_size if partial.is_file() else 0
    headers = {"User-Agent": f"DrewCraft-Launcher/{APP_VERSION}"}
    if existing:
        headers["Range"] = f"bytes={existing}-"
    req = urllib.request.Request(url, headers=headers)
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=120, context=_https_context()) as response:
        resumed = existing > 0 and getattr(response, "status", None) == 206
        if not resumed:
            existing = 0
        response_total = int(response.headers.get("Content-Length", "0") or 0)
        total = expected_size or (existing + response_total)
        downloaded = existing
        with partial.open("ab" if resumed else "wb") as out:
            while True:
                if cancelled and cancelled():
                    raise RuntimeError("download cancelled; partial data was kept for resume")
                chunk = response.read(1024 * 1024)
                if not chunk: break
                out.write(chunk)
                downloaded += len(chunk)
                elapsed = max(time.monotonic() - started, 0.001)
                rate = max(downloaded - existing, 1) / elapsed
                if progress:
                    progress({"phase": "download", "label": label or destination.name,
                              "downloaded": downloaded, "total": total, "bytesPerSecond": rate,
                              "etaSeconds": max(total - downloaded, 0) / rate if total else 0.0})
    if expected_size is not None and partial.stat().st_size != expected_size:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"download size mismatch for {url}")
    got = sha256_file(partial)
    if got != expected_sha:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"download hash mismatch for {url}: expected {expected_sha} got {got}")
    os.replace(partial, destination)


def _reuse_existing(entry: dict, app_dir: pathlib.Path, destination: pathlib.Path) -> bool:
    rel = pathlib.Path(*_safe_rel(entry["path"]).parts)
    releases = app_dir / "releases"
    if not releases.exists():
        return False
    for candidate in sorted(releases.glob("*/instance"), reverse=True):
        source = candidate / rel
        if verify_entry(source, entry):
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            return True
    return False


def install_pack(manifest: dict, app_dir: pathlib.Path, progress=None, cancelled=None) -> pathlib.Path:
    validate_manifest(manifest)
    version = manifest["packVersion"]
    release = app_dir / "releases" / version / "instance"
    stage = app_dir / "staging" / f"{version}.partial"
    stage.mkdir(parents=True, exist_ok=True)

    entries = selected_files(manifest)
    total_bytes = sum(entry["size"] for entry in entries)
    completed_bytes = 0
    for index, entry in enumerate(entries, start=1):
        if cancelled and cancelled(): raise RuntimeError("installation cancelled")
        target = stage / pathlib.Path(*_safe_rel(entry["path"]).parts)
        if progress:
            progress({"phase": "file", "label": entry["path"], "fileIndex": index, "fileCount": len(entries)})
        if verify_entry(target, entry):
            completed_bytes += entry["size"]
            continue
        if target.exists():
            target.unlink()
        if not _reuse_existing(entry, app_dir, target):
            def aggregate(event, base=completed_bytes):
                event = dict(event)
                event["overallDownloaded"] = base + event.get("downloaded", 0)
                event["overallTotal"] = total_bytes
                if progress: progress(event)
            download_verified(
                entry["url"], entry["sha256"], target, entry["size"],
                progress=aggregate, label=entry["path"], cancelled=cancelled,
            )
        completed_bytes += entry["size"]

    for entry in selected_files(manifest):
        target = stage / pathlib.Path(*_safe_rel(entry["path"]).parts)
        if not verify_entry(target, entry):
            raise RuntimeError(f"staged pack verification failed: {entry['path']}")

    if release.parent.exists():
        shutil.rmtree(release.parent)
    release.parent.mkdir(parents=True, exist_ok=True)
    os.replace(stage, release)
    return release


def _extract_archive(archive: pathlib.Path, destination: pathlib.Path, kind: str) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    if kind == "zip":
        with zipfile.ZipFile(archive) as zf:
            target = destination.resolve()
            for info in zf.infolist():
                resolved = (destination / info.filename).resolve()
                if target not in resolved.parents and resolved != target:
                    raise RuntimeError("unsafe runtime ZIP path")
            zf.extractall(destination)
    elif kind in ("tar.gz", "tgz"):
        with tarfile.open(archive, "r:gz") as tf:
            target = destination.resolve()
            for member in tf.getmembers():
                resolved = (destination / member.name).resolve()
                if target not in resolved.parents and resolved != target:
                    raise RuntimeError("unsafe runtime archive path")
            tf.extractall(destination)
    else:
        raise RuntimeError(f"unsupported runtime archive: {kind}")


def _find_runtime_executable(root: pathlib.Path, spec: dict) -> pathlib.Path:
    exact = spec.get("executable")
    if exact:
        candidate = root / pathlib.Path(*_safe_rel(exact).parts)
        if candidate.is_file():
            return candidate
    basename = spec.get("executableBasename")
    if not basename or pathlib.PurePath(basename).name != basename:
        raise RuntimeError("runtime spec requires executable or a safe executableBasename")
    matches = sorted(p for p in root.rglob(basename) if p.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"runtime executable {basename!r} resolved to {len(matches)} files under {root}")
    return matches[0]


def ensure_runtime_component(app_dir: pathlib.Path, name: str, spec: dict, progress=None, cancelled=None) -> pathlib.Path:
    version = str(spec["version"])
    root = app_dir / "runtime" / name / version
    marker = root / ".drewcraft-runtime.json"
    if marker.is_file():
        try:
            metadata = json.loads(marker.read_text("utf-8"))
            executable = _find_runtime_executable(root, spec)
            if (metadata.get("name") == name and metadata.get("version") == version
                    and metadata.get("archiveSha256") == spec["sha256"]
                    and metadata.get("executableSha256") == sha256_file(executable)):
                return executable
        except Exception:
            pass
    downloads = app_dir / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / f"{name}-{version}.{spec['archive'].replace('.', '-')}"
    if not archive.is_file() or sha256_file(archive) != spec["sha256"]:
        download_verified(
            spec["url"], spec["sha256"], archive, spec.get("size"),
            progress=progress, label=f"{name} runtime", cancelled=cancelled,
        )
    _extract_archive(archive, root, spec["archive"])
    executable = _find_runtime_executable(root, spec)
    if platform.system() != "Windows":
        executable.chmod(executable.stat().st_mode | 0o111)
    atomic_json(marker, {
        "name": name,
        "version": version,
        "archiveSha256": spec["sha256"],
        "executable": str(executable.relative_to(root)),
        "executableSha256": sha256_file(executable),
    })
    return executable


def ensure_runtime(manifest: dict, app_dir: pathlib.Path, progress=None, cancelled=None) -> dict:
    runtime = manifest.get("runtime", {})
    if not runtime:
        return {}
    platform_spec = runtime.get(platform_key())
    if not platform_spec:
        raise RuntimeError(f"release has no runtime bundle for {platform_key()}")
    java = ensure_runtime_component(app_dir, "java", platform_spec["java"], progress, cancelled)
    prism = ensure_runtime_component(app_dir, "prism", platform_spec["prism"], progress, cancelled)
    return {"java": str(java), "prism": str(prism)}


def _copy_preserved_user_data(previous_minecraft: pathlib.Path | None, target_minecraft: pathlib.Path) -> None:
    if previous_minecraft is None or not previous_minecraft.is_dir():
        return
    for rel in PRESERVED_USER_PATHS:
        source = previous_minecraft / rel
        target = target_minecraft / rel
        if not source.exists() or target.exists():
            continue
        if source.is_dir():
            if rel in HARDLINK_PRESERVED_PATHS:
                # Model assets are immutable and hash-validated by Terrain
                # Diffusion. Hard-linking avoids copying ~2 GiB on every
                # converge; copy2 remains the cross-filesystem fallback.
                def link_or_copy(src, dst):
                    try:
                        os.link(src, dst)
                    except OSError:
                        shutil.copy2(src, dst)

                shutil.copytree(source, target, copy_function=link_or_copy)
            else:
                shutil.copytree(source, target)
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def configure_prism_instance(instance_root: pathlib.Path, java_path: str | None, manifest: dict) -> str:
    instance_root.mkdir(parents=True, exist_ok=True)
    instance_id = instance_root.name
    # Managed memory is applied below with Prism's actual per-instance keys.
    # DrewCraft intentionally forces an 8 GiB heap on every convergence.
    cfg = instance_root / "instance.cfg"
    lines = [
        "InstanceType=OneSix",
        f"name=DrewCraft {manifest['packVersion']}",
        "MCLaunchMethod=LauncherPart",
    ]
    if java_path:
        lines.extend(["OverrideJavaLocation=true", f"JavaPath={java_path}"])
    cfg.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _apply_memory_settings(instance_root)

    mmc_pack = {
        "formatVersion": 1,
        "components": [
            {"uid": "net.minecraft", "version": manifest["minecraftVersion"], "important": True},
            {"uid": "net.neoforged", "version": manifest["loader"]["version"]},
        ],
    }
    atomic_json(instance_root / "mmc-pack.json", mmc_pack)
    return instance_id


def _previous_instance_minecraft(app_dir: pathlib.Path) -> pathlib.Path | None:
    state_path = app_dir / "state.json"
    if not state_path.is_file():
        return None
    try:
        state = json.loads(state_path.read_text("utf-8"))
        instance_id = state.get("instanceId")
        prism_root = state.get("prismRoot")
        if not instance_id or not prism_root:
            return None
        return pathlib.Path(prism_root) / "instances" / instance_id / "minecraft"
    except Exception:
        return None


def converge(live_url: str, app_dir: pathlib.Path, progress=None, cancelled=None) -> dict:
    app_dir.mkdir(parents=True, exist_ok=True)
    if progress:
        progress({"phase": "status", "label": "Checking for DrewCraft updates"})
    live = fetch_json(live_url)
    manifest_payload = fetch_bytes(live["manifestUrl"])
    got = sha256_bytes(manifest_payload)
    if got != live["manifestSha256"]:
        raise RuntimeError(f"release manifest hash mismatch expected={live['manifestSha256']} got={got}")
    manifest = json.loads(manifest_payload.decode("utf-8"))
    validate_manifest(manifest)
    if manifest["packVersion"] != live["packVersion"]:
        raise RuntimeError("stable pointer and manifest pack versions disagree")

    state_path = app_dir / "state.json"
    if state_path.is_file():
        try:
            existing_state = json.loads(state_path.read_text("utf-8"))
            if (existing_state.get("manifestSha256") == got
                    and not _local_failures(app_dir, manifest, existing_state)):
                runtime = ensure_runtime(manifest, app_dir, progress, cancelled)
                existing_state["prismExecutable"] = runtime.get("prism")
                existing_state["javaExecutable"] = runtime.get("java")
                atomic_json(state_path, existing_state)
                _apply_memory_settings(
                    pathlib.Path(existing_state["prismRoot"]) / "instances" / existing_state["instanceId"])
                if progress: progress({"phase": "complete", "label": "DrewCraft is already up to date"})
                return existing_state
        except Exception:
            pass

    previous_minecraft = _previous_instance_minecraft(app_dir)
    release_instance = install_pack(manifest, app_dir, progress, cancelled)
    if progress:
        progress({"phase": "status", "label": "Preparing Java and Prism Launcher"})
    runtime = ensure_runtime(manifest, app_dir, progress, cancelled)
    prism_root = app_dir / "prism-data"
    instances_root = prism_root / "instances"
    instances_root.mkdir(parents=True, exist_ok=True)
    instance_id = f"DrewCraft-{manifest['packVersion']}"
    managed_instance = instances_root / instance_id
    stage_instance = instances_root / f".{instance_id}.partial"
    if stage_instance.exists():
        shutil.rmtree(stage_instance)
    shutil.copytree(release_instance, stage_instance / "minecraft")
    _copy_preserved_user_data(previous_minecraft, stage_instance / "minecraft")
    configure_prism_instance(stage_instance, runtime.get("java"), manifest)

    if managed_instance.exists():
        shutil.rmtree(managed_instance)
    _replace_path(stage_instance, managed_instance)
    _ensure_managed_resource_packs(managed_instance / "minecraft")

    state = {
        "launcherVersion": APP_VERSION,
        "packVersion": manifest["packVersion"],
        "protocolVersion": manifest["protocolVersion"],
        "manifestSha256": got,
        "liveUrl": live_url,
        "prismRoot": str(prism_root),
        "instanceId": instance_id,
        "prismExecutable": runtime.get("prism"),
        "javaExecutable": runtime.get("java"),
        "server": manifest.get("server", {}),
    }
    atomic_json(app_dir / "state.json", state)
    if progress:
        progress({"phase": "complete", "label": "DrewCraft is ready"})
    return state


MANAGED_RESOURCE_PACKS = ("drewcraft_cult_first_pass",)


MANAGED_MEMORY = (
    ("OverrideMemory", "true"),
    ("MinMemAlloc", "8192"),
    ("MaxMemAlloc", "8192"),
)
"""Managed client RAM: exactly 8 GiB.

Prism's instance keys are MinMemAlloc/MaxMemAlloc. OverrideMemory=true
forces these instance values instead of inheriting the global Prism default.
"""


def _apply_memory_settings(instance_root: pathlib.Path) -> None:
    """Idempotently enforce managed RAM in an existing instance.cfg.

    Fresh instances get it from configure_prism_instance; pre-existing
    instances (created before this policy) get repaired here on every
    converge, including the up-to-date fast path that rebuilds nothing.
    """
    cfg = instance_root / "instance.cfg"
    try:
        text = cfg.read_text(encoding="utf-8") if cfg.is_file() else ""
    except OSError:
        return
    lines = text.splitlines()
    # v0.1.5 accidentally wrote non-Prism keys MinMem/MaxMem. Remove them so
    # old installs cannot display a misleading 4096 value after repair.
    legacy_prefixes = ("MinMem=", "MaxMem=")
    filtered = [line for line in lines if not line.startswith(legacy_prefixes)]
    changed = filtered != lines
    lines = filtered
    for key, value in MANAGED_MEMORY:
        for index, line in enumerate(lines):
            if line.startswith(key + "="):
                if line != f"{key}={value}":
                    lines[index] = f"{key}={value}"
                    changed = True
                break
        else:
            lines.append(f"{key}={value}")
            changed = True
    if changed or not cfg.is_file():
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _ensure_managed_resource_packs(minecraft_dir: pathlib.Path) -> None:
    # DrewCraft-owned resource packs ship inside the release but live in the
    # user-preserved resourcepacks/ tree, so installation alone does not
    # enable them. Ensure our packs are active without touching the player's
    # other choices. Missing pack directories are skipped (older releases).
    options = minecraft_dir / "options.txt"
    try:
        text = options.read_text("utf-8") if options.is_file() else ""
    except OSError:
        return
    wanted = [f"file/{name}" for name in MANAGED_RESOURCE_PACKS
              if (minecraft_dir / "resourcepacks" / name / "pack.mcmeta").is_file()]
    if not wanted:
        return
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("resourcePacks:"):
            try:
                active = json.loads(line.split(":", 1)[1])
            except ValueError:
                active = []
            if not isinstance(active, list):
                active = []
            changed = False
            for pack in wanted:
                if pack not in active:
                    active.append(pack)
                    changed = True
            if changed:
                lines[index] = "resourcePacks:" + json.dumps(active)
                options.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    lines.append("resourcePacks:" + json.dumps(["vanilla", *wanted]))
    options.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_local(app_dir: pathlib.Path, live_url: str | None = None) -> list[str]:
    state_path = app_dir / "state.json"
    if not state_path.exists():
        return ["state.json missing"]
    state = json.loads(state_path.read_text("utf-8"))
    if live_url is None:
        live_url = state["liveUrl"]
    live = fetch_json(live_url)
    payload = fetch_bytes(live["manifestUrl"])
    if sha256_bytes(payload) != live["manifestSha256"]:
        return ["manifest hash mismatch"]
    manifest = json.loads(payload.decode("utf-8"))
    validate_manifest(manifest)

    return _local_failures(app_dir, manifest, state)


def _local_failures(app_dir: pathlib.Path, manifest: dict, state: dict) -> list[str]:
    release_root = app_dir / "releases" / manifest["packVersion"] / "instance"
    prism_instance = pathlib.Path(state["prismRoot"]) / "instances" / state["instanceId"]
    prism_minecraft = prism_instance / "minecraft"
    failures: set[str] = set()
    for entry in selected_files(manifest):
        rel = pathlib.Path(*_safe_rel(entry["path"]).parts)
        if not verify_entry(release_root / rel, entry) or not verify_entry(prism_minecraft / rel, entry):
            failures.add(entry["path"])
    if not (prism_instance / "mmc-pack.json").is_file():
        failures.add("prism:mmc-pack.json")
    if not (prism_instance / "instance.cfg").is_file():
        failures.add("prism:instance.cfg")
    return sorted(failures)


def server_ready(state: dict) -> tuple[bool, str]:
    health_url = state.get("server", {}).get("healthUrl")
    if not health_url:
        return True, "no health URL configured"
    try:
        health = fetch_json(health_url)
    except Exception as exc:
        return False, f"server offline/unreachable: {exc}"
    if health.get("status") != "ready":
        return False, f"server status is {health.get('status', 'unknown')}"
    if health.get("protocolVersion") != state["protocolVersion"]:
        return False, "server/client protocol mismatch"
    if health.get("packVersion") != state["packVersion"]:
        return False, "server/client pack mismatch"
    return True, "ready"


def launch(app_dir: pathlib.Path) -> int:
    state = json.loads((app_dir / "state.json").read_text("utf-8"))
    ok, message = server_ready(state)
    if not ok:
        raise RuntimeError(message)
    prism = state.get("prismExecutable")
    if not prism:
        raise RuntimeError("managed Prism runtime is not configured")
    cmd = [prism, "--dir", state["prismRoot"], "--launch", state["instanceId"]]
    address = state.get("server", {}).get("address")
    if address:
        cmd += ["--server", address]
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(prog="DrewCraft")
    parser.add_argument("--app-dir", default=str(default_app_dir()))
    parser.add_argument("--live-url")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("install")
    sub.add_parser("update")
    sub.add_parser("repair")
    sub.add_parser("verify")
    sub.add_parser("launch")
    sub.add_parser("status")
    args = parser.parse_args()
    app_dir = pathlib.Path(args.app_dir)

    if args.command in ("install", "update", "repair"):
        live_url = args.live_url
        if not live_url and (app_dir / "state.json").exists():
            live_url = json.loads((app_dir / "state.json").read_text("utf-8")).get("liveUrl")
        if not live_url:
            raise RuntimeError("--live-url is required for first install")
        state = converge(live_url, app_dir)
        print(json.dumps({"ok": True, "packVersion": state["packVersion"]}))
        return 0
    if args.command == "verify":
        failures = verify_local(app_dir, args.live_url)
        print(json.dumps({"ok": not failures, "failures": failures}))
        return 0 if not failures else 2
    if args.command == "launch":
        return launch(app_dir)
    if args.command == "status":
        state = json.loads((app_dir / "state.json").read_text("utf-8"))
        ok, message = server_ready(state)
        print(json.dumps({"ok": ok, "message": message, **state}, sort_keys=True))
        return 0 if ok else 3
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"DrewCraft: {exc}", file=sys.stderr)
        raise SystemExit(1)
