#!/usr/bin/env python3
"""Atomic DrewCraft server release/update/backup/restore helper."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))
from release_contract import load_json, selected_files, sha256_file, validate_manifest, verify_tree  # noqa: E402

WORLD_INFO = "drewcraft-world.json"


def _download(url: str, target: pathlib.Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "DrewCraft-ServerCtl/1"})
    with urllib.request.urlopen(req, timeout=180) as response, target.open("wb") as out:
        shutil.copyfileobj(response, out)


def _atomic_json(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, sort_keys=True, separators=(",", ":"))
            fh.write("\n")
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def ensure_layout(root: pathlib.Path) -> None:
    for rel in ("releases", "staging", "persistent/world", "backups", "logs", "state"):
        (root / rel).mkdir(parents=True, exist_ok=True)


def read_world_identity(root: pathlib.Path) -> dict:
    path = root / "persistent" / "world" / WORLD_INFO
    if not path.is_file():
        raise RuntimeError(f"persistent world is missing {WORLD_INFO}")
    identity = json.loads(path.read_text("utf-8"))
    if identity.get("schemaVersion") != 1:
        raise RuntimeError("unsupported DrewCraft world identity schema")
    return identity


def require_world_identity(root: pathlib.Path, manifest: dict) -> dict:
    identity = read_world_identity(root)
    expected = manifest["world"]
    for key in ("worldId", "worldRevision", "generationPackVersion"):
        if identity.get(key) != expected.get(key):
            raise RuntimeError(
                f"world/release mismatch for {key}: world={identity.get(key)!r} release={expected.get(key)!r}"
            )
    return identity


def stage_release(root: pathlib.Path, manifest: dict) -> pathlib.Path:
    validate_manifest(manifest)
    ensure_layout(root)
    version = manifest["packVersion"]
    final = root / "releases" / version
    if final.exists():
        failures = verify_tree(final, manifest, "server")
        if failures:
            raise RuntimeError(f"existing release {version} is corrupt: {failures}")
        return final

    staging = root / "staging" / f"{version}.partial"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for entry in selected_files(manifest, "server"):
        target = staging / entry["path"]
        _download(entry["url"], target)
        if target.stat().st_size != entry["size"] or sha256_file(target) != entry["sha256"]:
            raise RuntimeError(f"download verification failed for {entry['path']}")
    failures = verify_tree(staging, manifest, "server")
    if failures:
        raise RuntimeError(f"staged release verification failed: {failures}")
    (staging / ".drewcraft-release-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(staging, final)
    return final


def _current_target(root: pathlib.Path) -> pathlib.Path | None:
    current = root / "current"
    if not current.exists() and not current.is_symlink():
        return None
    return current.resolve()


def _wire_persistent_paths(root: pathlib.Path, release: pathlib.Path) -> None:
    for name, target in (("world", root / "persistent" / "world"), ("logs", root / "logs")):
        link = release / name
        if link.exists() or link.is_symlink():
            if link.is_symlink() and link.resolve() == target.resolve():
                continue
            raise RuntimeError(f"release contains reserved persistent path {name!r}")
        os.symlink(target.resolve(), link, target_is_directory=True)


def activate(root: pathlib.Path, release: pathlib.Path, manifest: dict) -> pathlib.Path | None:
    ensure_layout(root)
    require_world_identity(root, manifest)
    _wire_persistent_paths(root, release)
    previous = _current_target(root)
    link = root / "current"
    temp_link = root / ".current.next"
    if temp_link.exists() or temp_link.is_symlink():
        temp_link.unlink()
    os.symlink(release.resolve(), temp_link, target_is_directory=True)
    os.replace(temp_link, link)
    _atomic_json(root / "state" / "active-release.json", {
        "packVersion": manifest["packVersion"],
        "protocolVersion": manifest["protocolVersion"],
        "worldId": manifest["world"]["worldId"],
        "worldRevision": manifest["world"]["worldRevision"],
        "releasePath": str(release.resolve()),
        "previousReleasePath": str(previous) if previous else None,
    })
    return previous


def rollback_application(root: pathlib.Path, previous: pathlib.Path | None) -> None:
    if previous is None:
        raise RuntimeError("no previous application release to roll back to")
    if not previous.is_dir():
        raise RuntimeError(f"previous release is unavailable: {previous}")
    temp_link = root / ".current.rollback"
    if temp_link.exists() or temp_link.is_symlink():
        temp_link.unlink()
    os.symlink(previous.resolve(), temp_link, target_is_directory=True)
    os.replace(temp_link, root / "current")


def backup(root: pathlib.Path, manifest: dict, *, label: str = "manual") -> pathlib.Path:
    ensure_layout(root)
    identity = require_world_identity(root, manifest)
    persistent = root / "persistent"
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = root / "backups" / f"{stamp}-{label}.tar.gz"
    meta = {
        "schemaVersion": 1,
        "createdUtc": stamp,
        "packVersion": manifest["packVersion"],
        "protocolVersion": manifest["protocolVersion"],
        "world": identity,
    }
    _atomic_json(persistent / ".drewcraft-backup-metadata.json", meta)
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(persistent, arcname="persistent")
    digest = sha256_file(archive)
    archive.with_suffix(archive.suffix + ".sha256").write_text(digest + "\n", encoding="ascii")
    _atomic_json(archive.with_suffix(archive.suffix + ".json"), {**meta, "sha256": digest})
    return archive


def restore_backup(archive: pathlib.Path, target_root: pathlib.Path) -> pathlib.Path:
    expected_file = archive.with_suffix(archive.suffix + ".sha256")
    if not expected_file.is_file():
        raise RuntimeError("backup checksum is missing")
    expected = expected_file.read_text("ascii").strip()
    got = sha256_file(archive)
    if got != expected:
        raise RuntimeError(f"backup hash mismatch expected={expected} got={got}")
    target = target_root / "persistent"
    if target.exists() and any(target.iterdir()):
        raise RuntimeError("restore target persistent directory is not empty")
    target_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tf:
        base = target_root.resolve()
        for member in tf.getmembers():
            resolved = (target_root / member.name).resolve()
            if base not in resolved.parents and resolved != base:
                raise RuntimeError("unsafe path in backup archive")
        tf.extractall(target_root)
    if not (target / "world" / WORLD_INFO).is_file():
        raise RuntimeError("restored backup is missing DrewCraft world identity")
    return target


def run_cmd(command: str | None) -> None:
    if command:
        subprocess.run(command, shell=True, check=True)


def write_health(root: pathlib.Path, status: str, manifest: dict, message: str = "") -> dict:
    payload = {
        "status": status,
        "packVersion": manifest["packVersion"],
        "protocolVersion": manifest["protocolVersion"],
        "minecraftVersion": manifest["minecraftVersion"],
        "worldId": manifest["world"]["worldId"],
        "worldRevision": manifest["world"]["worldRevision"],
        "message": message,
    }
    _atomic_json(root / "state" / "health.json", payload)
    return payload


def update_transaction(root: pathlib.Path, manifest: dict, *, stop_command: str | None = None,
                       start_command: str | None = None, health_command: str | None = None) -> dict:
    require_world_identity(root, manifest)
    release = stage_release(root, manifest)
    write_health(root, "updating", manifest)
    archive = backup(root, manifest, label="pre-update")
    run_cmd(stop_command)
    previous = activate(root, release, manifest)
    try:
        run_cmd(start_command)
        run_cmd(health_command)
    except Exception:
        rollback_application(root, previous)
        write_health(root, "rollback", manifest, "application rollout failed; persistent world was not rolled back")
        if start_command and previous is not None:
            run_cmd(start_command)
        raise
    write_health(root, "ready", manifest)
    return {"release": str(release), "backup": str(archive), "previous": str(previous) if previous else None}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="/srv/drewcraft")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("stage"); s.add_argument("manifest")
    a = sub.add_parser("activate"); a.add_argument("manifest")
    b = sub.add_parser("backup"); b.add_argument("manifest"); b.add_argument("--label", default="manual")
    r = sub.add_parser("restore"); r.add_argument("archive"); r.add_argument("--target-root", required=True)
    u = sub.add_parser("update"); u.add_argument("manifest"); u.add_argument("--stop-command"); u.add_argument("--start-command"); u.add_argument("--health-command")
    args = p.parse_args()
    root = pathlib.Path(args.root)
    if args.command == "restore":
        print(restore_backup(pathlib.Path(args.archive), pathlib.Path(args.target_root)))
        return 0
    manifest = validate_manifest(load_json(args.manifest))
    if args.command == "stage": print(stage_release(root, manifest))
    elif args.command == "activate": print(activate(root, stage_release(root, manifest), manifest))
    elif args.command == "backup": print(backup(root, manifest, label=args.label))
    elif args.command == "update":
        print(json.dumps(update_transaction(root, manifest, stop_command=args.stop_command,
                                            start_command=args.start_command, health_command=args.health_command), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
