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
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile

APP_VERSION = "0.1.2"
PRESERVED_USER_PATHS = ("screenshots", "resourcepacks", "shaderpacks", "saves", "options.txt")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_bytes(url: str, progress=None, label: str = "download") -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"DrewCraft-Launcher/{APP_VERSION}"})
    with urllib.request.urlopen(req, timeout=120) as response:
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
    for entry in manifest["files"]:
        _safe_rel(entry["path"])
        if entry["side"] not in ("common", "client", "server"):
            raise RuntimeError("Malformed release side")


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
                      expected_size: int | None = None, progress=None, label: str | None = None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = fetch_bytes(url, progress=progress, label=label or destination.name)
    if expected_size is not None and len(payload) != expected_size:
        raise RuntimeError(f"download size mismatch for {url}")
    got = sha256_bytes(payload)
    if got != expected_sha:
        raise RuntimeError(f"download hash mismatch for {url}: expected {expected_sha} got {got}")
    destination.write_bytes(payload)


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


def install_pack(manifest: dict, app_dir: pathlib.Path, progress=None) -> pathlib.Path:
    validate_manifest(manifest)
    version = manifest["packVersion"]
    release = app_dir / "releases" / version / "instance"
    stage = app_dir / "staging" / f"{version}.partial"
    stage.mkdir(parents=True, exist_ok=True)

    entries = selected_files(manifest)
    for index, entry in enumerate(entries, start=1):
        target = stage / pathlib.Path(*_safe_rel(entry["path"]).parts)
        if progress:
            progress({"phase": "file", "label": entry["path"], "fileIndex": index, "fileCount": len(entries)})
        if verify_entry(target, entry):
            continue
        if target.exists():
            target.unlink()
        if not _reuse_existing(entry, app_dir, target):
            download_verified(
                entry["url"], entry["sha256"], target, entry["size"],
                progress=progress, label=entry["path"],
            )

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


def ensure_runtime_component(app_dir: pathlib.Path, name: str, spec: dict, progress=None) -> pathlib.Path:
    version = str(spec["version"])
    root = app_dir / "runtime" / name / version
    marker = root / ".drewcraft-runtime.json"
    if marker.is_file():
        executable = _find_runtime_executable(root, spec)
        return executable
    downloads = app_dir / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / f"{name}-{version}.{spec['archive'].replace('.', '-')}"
    if not archive.is_file() or sha256_file(archive) != spec["sha256"]:
        download_verified(
            spec["url"], spec["sha256"], archive, spec.get("size"),
            progress=progress, label=f"{name} runtime",
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
    })
    return executable


def ensure_runtime(manifest: dict, app_dir: pathlib.Path, progress=None) -> dict:
    runtime = manifest.get("runtime", {})
    if not runtime:
        return {}
    platform_spec = runtime.get(platform_key())
    if not platform_spec:
        raise RuntimeError(f"release has no runtime bundle for {platform_key()}")
    java = ensure_runtime_component(app_dir, "java", platform_spec["java"], progress)
    prism = ensure_runtime_component(app_dir, "prism", platform_spec["prism"], progress)
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
            shutil.copytree(source, target)
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def configure_prism_instance(instance_root: pathlib.Path, java_path: str | None, manifest: dict) -> str:
    instance_root.mkdir(parents=True, exist_ok=True)
    instance_id = instance_root.name
    cfg = instance_root / "instance.cfg"
    lines = [
        "InstanceType=OneSix",
        f"name=DrewCraft {manifest['packVersion']}",
        "MCLaunchMethod=LauncherPart",
    ]
    if java_path:
        lines.extend(["OverrideJavaLocation=true", f"JavaPath={java_path}"])
    cfg.write_text("\n".join(lines) + "\n", encoding="utf-8")

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


def converge(live_url: str, app_dir: pathlib.Path, progress=None) -> dict:
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

    previous_minecraft = _previous_instance_minecraft(app_dir)
    release_instance = install_pack(manifest, app_dir, progress)
    if progress:
        progress({"phase": "status", "label": "Preparing Java and Prism Launcher"})
    runtime = ensure_runtime(manifest, app_dir, progress)
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
    os.replace(stage_instance, managed_instance)

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
