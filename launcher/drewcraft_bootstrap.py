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
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

APP_VERSION = "0.1.0"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"DrewCraft-Launcher/{APP_VERSION}"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def platform_key() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows" and machine in ("amd64", "x86_64"):
        return "windows-x86_64"
    if system == "darwin" and machine in ("arm64", "aarch64"):
        return "macos-arm64"
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


def validate_manifest(manifest: dict) -> None:
    if manifest.get("schemaVersion") != 1:
        raise RuntimeError("Unsupported DrewCraft release manifest")
    if manifest.get("java", {}).get("major") != 21:
        raise RuntimeError("DrewCraft release does not declare Java 21")
    if not manifest.get("packVersion") or not isinstance(manifest.get("files"), list):
        raise RuntimeError("Malformed DrewCraft release manifest")
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


def download_verified(url: str, expected_sha: str, destination: pathlib.Path, expected_size: int | None = None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = fetch_bytes(url)
    if expected_size is not None and len(payload) != expected_size:
        raise RuntimeError(f"download size mismatch for {url}")
    got = sha256_bytes(payload)
    if got != expected_sha:
        raise RuntimeError(f"download hash mismatch for {url}: expected {expected_sha} got {got}")
    destination.write_bytes(payload)


def install_pack(manifest: dict, app_dir: pathlib.Path) -> pathlib.Path:
    validate_manifest(manifest)
    version = manifest["packVersion"]
    release = app_dir / "releases" / version / "instance"
    stage = app_dir / "staging" / f"{version}.partial"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)

    for entry in selected_files(manifest):
        target = stage / pathlib.Path(*_safe_rel(entry["path"]).parts)
        download_verified(entry["url"], entry["sha256"], target, entry["size"])

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


def ensure_runtime_component(app_dir: pathlib.Path, name: str, spec: dict) -> pathlib.Path:
    version = str(spec["version"])
    root = app_dir / "runtime" / name / version
    executable = root / pathlib.Path(*_safe_rel(spec["executable"]).parts)
    if executable.exists():
        return executable
    downloads = app_dir / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / f"{name}-{version}.{spec['archive'].replace('.', '-')}"
    download_verified(spec["url"], spec["sha256"], archive, spec.get("size"))
    _extract_archive(archive, root, spec["archive"])
    if not executable.exists():
        raise RuntimeError(f"{name} archive did not contain expected executable {spec['executable']}")
    if platform.system() != "Windows":
        executable.chmod(executable.stat().st_mode | 0o111)
    return executable


def ensure_runtime(manifest: dict, app_dir: pathlib.Path) -> dict:
    runtime = manifest.get("runtime", {})
    if not runtime:
        return {}
    platform_spec = runtime.get(platform_key())
    if not platform_spec:
        raise RuntimeError(f"release has no runtime bundle for {platform_key()}")
    java = ensure_runtime_component(app_dir, "java", platform_spec["java"])
    prism = ensure_runtime_component(app_dir, "prism", platform_spec["prism"])
    return {"java": str(java), "prism": str(prism)}


def configure_prism_instance(instance_dir: pathlib.Path, java_path: str | None) -> str:
    instance_id = instance_dir.parent.name
    cfg = instance_dir.parent / "instance.cfg"
    lines = ["InstanceType=OneSix", f"name=DrewCraft {instance_id}"]
    if java_path:
        lines.extend(["OverrideJavaLocation=true", f"JavaPath={java_path}"])
    cfg.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return instance_id


def converge(live_url: str, app_dir: pathlib.Path) -> dict:
    app_dir.mkdir(parents=True, exist_ok=True)
    live = fetch_json(live_url)
    manifest_payload = fetch_bytes(live["manifestUrl"])
    got = sha256_bytes(manifest_payload)
    if got != live["manifestSha256"]:
        raise RuntimeError(f"release manifest hash mismatch expected={live['manifestSha256']} got={got}")
    manifest = json.loads(manifest_payload.decode("utf-8"))
    validate_manifest(manifest)
    if manifest["packVersion"] != live["packVersion"]:
        raise RuntimeError("stable pointer and manifest pack versions disagree")

    release_instance = install_pack(manifest, app_dir)
    runtime = ensure_runtime(manifest, app_dir)
    prism_root = app_dir / "prism-data"
    managed_instance = prism_root / "instances" / f"DrewCraft-{manifest['packVersion']}"
    if managed_instance.exists():
        shutil.rmtree(managed_instance)
    managed_instance.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(release_instance, managed_instance / "minecraft")
    instance_id = configure_prism_instance(managed_instance / "minecraft", runtime.get("java"))

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
    base = app_dir / "releases" / manifest["packVersion"] / "instance"
    failures = []
    for entry in selected_files(manifest):
        path = base / pathlib.Path(*_safe_rel(entry["path"]).parts)
        if not verify_entry(path, entry):
            failures.append(entry["path"])
    return failures


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
        raise RuntimeError("managed Prism runtime is not configured in this development manifest")
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
