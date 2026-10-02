#!/usr/bin/env python3
"""Atomic DrewCraft server release/update/backup/restore helper."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import pwd
import re
import secrets
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
RELEASE_MANIFEST = ".drewcraft-release-manifest.json"


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
    for rel in (
        "releases", "staging", "persistent/world",
        "persistent/terrain-diffusion-models", "persistent/terrain-diffusion-cache",
        "persistent/operator",
        "backups", "logs", "state",
    ):
        (root / rel).mkdir(parents=True, exist_ok=True)


def _tree_bytes(root: pathlib.Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file()) if root.exists() else 0


def require_free_space(root: pathlib.Path, required_bytes: int, operation: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(root).free
    # Keep 1 GiB for logs, temporary files, and the operating system.
    if free < required_bytes + 1024 ** 3:
        raise RuntimeError(f"insufficient disk space for {operation}: need {required_bytes + 1024 ** 3}, free {free}")


def _prepare_service_permissions(release: pathlib.Path) -> None:
    """Keep executable modes and service ownership after HTTP artifact staging."""
    runner = release / "run.sh"
    if runner.is_file():
        runner.chmod(0o755)
    if os.name != "posix" or os.geteuid() != 0:
        return
    try:
        account = pwd.getpwnam("drewcraft")
    except KeyError:
        return  # CI fixtures have no production service account.
    for current, directories, files in os.walk(release, followlinks=False):
        os.chown(current, account.pw_uid, account.pw_gid)
        for name in directories + files:
            os.chown(pathlib.Path(current) / name, account.pw_uid, account.pw_gid,
                     follow_symlinks=False)


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
    require_free_space(root, sum(entry["size"] for entry in selected_files(manifest, "server")), "release staging")
    version = manifest["packVersion"]
    final = root / "releases" / version
    if final.exists():
        failures = verify_tree(final, manifest, "server")
        if failures:
            raise RuntimeError(f"existing release {version} is corrupt: {failures}")
        _prepare_service_permissions(final)
        return final

    staging = root / "staging" / f"{version}.partial"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    current = _current_target(root)
    for entry in selected_files(manifest, "server"):
        target = staging / entry["path"]
        cached = current / entry["path"] if current is not None else None
        if (cached is not None and cached.is_file() and not cached.is_symlink()
                and cached.stat().st_size == entry["size"]
                and sha256_file(cached) == entry["sha256"]):
            target.parent.mkdir(parents=True, exist_ok=True)
            # Copies, never hardlinks: runtime config writes must not mutate
            # the retained application used for rollback.
            shutil.copy2(cached, target)
        else:
            _download(entry["url"], target)
        if target.stat().st_size != entry["size"] or sha256_file(target) != entry["sha256"]:
            raise RuntimeError(f"download verification failed for {entry['path']}")
        if entry["path"] == "run.sh":
            target.chmod(0o755)
    failures = verify_tree(staging, manifest, "server")
    if failures:
        raise RuntimeError(f"staged release verification failed: {failures}")
    (staging / RELEASE_MANIFEST).write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(staging, final)
    _prepare_service_permissions(final)
    return final


def _current_target(root: pathlib.Path) -> pathlib.Path | None:
    current = root / "current"
    if not current.exists() and not current.is_symlink():
        return None
    return current.resolve()


def _wire_persistent_paths(root: pathlib.Path, release: pathlib.Path) -> None:
    for name, target in (
        ("world", root / "persistent" / "world"),
        ("logs", root / "logs"),
        ("terrain-diffusion-models", root / "persistent" / "terrain-diffusion-models"),
        ("terrain-diffusion-cache", root / "persistent" / "terrain-diffusion-cache"),
    ):
        link = release / name
        if link.exists() or link.is_symlink():
            if link.is_symlink() and link.resolve() == target.resolve():
                continue
            raise RuntimeError(f"release contains reserved persistent path {name!r}")
        os.symlink(target.resolve(), link, target_is_directory=True)
    for name in ("ops.json", "whitelist.json", "banned-ips.json", "banned-players.json"):
        target = root / "persistent" / "operator" / name
        if not target.exists():
            target.write_text("[]\n", encoding="utf-8")
        link = release / name
        if link.exists() or link.is_symlink():
            if link.is_symlink() and link.resolve() == target.resolve():
                continue
            raise RuntimeError(f"release contains reserved persistent path {name!r}")
        os.symlink(target.resolve(), link)


def _active_state(root: pathlib.Path, release: pathlib.Path, manifest: dict, previous: pathlib.Path | None) -> dict:
    return {
        "packVersion": manifest["packVersion"],
        "protocolVersion": manifest["protocolVersion"],
        "worldId": manifest["world"]["worldId"],
        "worldRevision": manifest["world"]["worldRevision"],
        "releasePath": str(release.resolve()),
        "previousReleasePath": str(previous) if previous else None,
    }


def _replace_link(temp_link: pathlib.Path, dest: pathlib.Path) -> None:
    # os.replace() cannot atomically replace an existing directory symlink on
    # Windows (WinError 5). Unlink the destination first on Windows; POSIX
    # keeps the atomic replace path.
    if os.name == "nt" and (dest.exists() or dest.is_symlink()):
        dest.unlink()
    os.replace(temp_link, dest)


def require_storage_compatibility(root: pathlib.Path, manifest: dict) -> None:
    state_path = root / 'state/world-storage.json'
    state = load_json(state_path) if state_path.exists() else {}
    actual_linear = state.get('format') == 'linear-v1' or any(
        (root / 'persistent/world').rglob('r.*.*.linear'))
    target = manifest.get('worldStorage', {}).get('format', 'anvil')
    has_linear = any(entry['path'].startswith('mods/linear-')
                     for entry in selected_files(manifest, 'server'))
    if actual_linear and (target != 'linear-v1' or not has_linear):
        raise RuntimeError('Refusing Anvil-only application against Linear world; restore world before rollback')
    if target == 'linear-v1':
        if not has_linear:
            raise RuntimeError('Linear storage release lacks its exact server mod')
        if not actual_linear and any((root / 'persistent/world').rglob('*.mca')):
            if not state.get('migrationAuthorized') or not (root / 'state/backup-hold.json').exists():
                raise RuntimeError('Anvil conversion requires explicit protected world-format transaction')


def activate(root: pathlib.Path, release: pathlib.Path, manifest: dict) -> pathlib.Path | None:
    require_storage_compatibility(root, manifest)
    ensure_layout(root)
    require_world_identity(root, manifest)
    _wire_persistent_paths(root, release)
    previous = _current_target(root)
    link = root / "current"
    temp_link = root / ".current.next"
    if temp_link.exists() or temp_link.is_symlink():
        temp_link.unlink()
    os.symlink(release.resolve(), temp_link, target_is_directory=True)
    _replace_link(temp_link, link)
    _atomic_json(root / "state" / "active-release.json", _active_state(root, release, manifest, previous))
    return previous


def _manifest_for_release(release: pathlib.Path) -> dict:
    path = release / RELEASE_MANIFEST
    if not path.is_file():
        raise RuntimeError(f"release is missing {RELEASE_MANIFEST}: {release}")
    return validate_manifest(json.loads(path.read_text("utf-8")))


def rollback_application(root: pathlib.Path, previous: pathlib.Path | None) -> dict | None:
    current = root / "current"
    failed = _current_target(root)
    if previous is None:
        if current.exists() or current.is_symlink():
            current.unlink()
        (root / "state" / "active-release.json").unlink(missing_ok=True)
        return None
    if not previous.is_dir():
        raise RuntimeError(f"previous release is unavailable: {previous}")

    manifest = _manifest_for_release(previous)
    require_storage_compatibility(root, manifest)
    require_world_identity(root, manifest)
    temp_link = root / ".current.rollback"
    if temp_link.exists() or temp_link.is_symlink():
        temp_link.unlink()
    os.symlink(previous.resolve(), temp_link, target_is_directory=True)
    _replace_link(temp_link, current)
    _atomic_json(
        root / "state" / "active-release.json",
        _active_state(root, previous, manifest, failed if failed != previous else None),
    )
    return manifest


def backup(root: pathlib.Path, manifest: dict, *, label: str = "manual", retain: int = 1,
           copy_dir: pathlib.Path | None = None) -> pathlib.Path:
    require_backup_unpinned(root)
    if retain != 1:
        raise RuntimeError("DrewCraft backup policy requires exactly one restore point")
    if (root / "state/backup-config.json").exists():
        return backup_restic(root, manifest, label=label, copy_dir=copy_dir)
    ensure_layout(root)
    identity = require_world_identity(root, manifest)
    persistent = root / "persistent"
    require_free_space(root, _tree_bytes(persistent), "world backup")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    archive = root / "backups" / f"{stamp}-{label}.tar.gz"
    meta = {
        "schemaVersion": 1,
        "createdUtc": stamp,
        "packVersion": manifest["packVersion"],
        "protocolVersion": manifest["protocolVersion"],
        "world": identity,
    }
    _atomic_json(persistent / ".drewcraft-backup-metadata.json", meta)
    with tarfile.open(archive, "w:gz", compresslevel=9) as tf:
        tf.add(persistent, arcname="persistent")
    digest = sha256_file(archive)
    archive.with_suffix(archive.suffix + ".sha256").write_text(digest + "\n", encoding="ascii")
    _atomic_json(archive.with_suffix(archive.suffix + ".json"), {**meta, "sha256": digest})
    if copy_dir is not None:
        copy_dir.mkdir(parents=True, exist_ok=True)
        for source in (archive, archive.with_suffix(archive.suffix + ".sha256"), archive.with_suffix(archive.suffix + ".json")):
            shutil.copy2(source, copy_dir / source.name)
    if retain > 0:
        archives = sorted((root / "backups").glob("*.tar.gz"), reverse=True)
        for stale in archives[retain:]:
            stale.unlink(missing_ok=True)
            stale.with_suffix(stale.suffix + ".sha256").unlink(missing_ok=True)
            stale.with_suffix(stale.suffix + ".json").unlink(missing_ok=True)
    return archive


def restore_backup(archive: pathlib.Path, target_root: pathlib.Path) -> pathlib.Path:
    if archive.name.endswith(".restic.json"):
        return restore_restic(archive, target_root)
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
        tf.extractall(target_root, filter="data")
    if not (target / "world" / WORLD_INFO).is_file():
        raise RuntimeError("restored backup is missing DrewCraft world identity")
    return target


def restic_run(config: dict, *args: str, cwd: pathlib.Path | None = None) -> str:
    if config.get("backend") != "restic":
        raise RuntimeError("unsupported configured backup backend")
    result = subprocess.run([
        "restic", "--no-cache", "--repo", config["repository"],
        "--password-file", config["passwordFile"], "--compression", "max", *args,
    ], cwd=cwd, check=True, text=True, stdout=subprocess.PIPE)
    return result.stdout


def init_restic(root: pathlib.Path, password_file: pathlib.Path) -> dict:
    ensure_layout(root)
    config_path = root / "state/backup-config.json"
    if config_path.exists():
        raise RuntimeError("backup backend already configured")
    repository = root.resolve() / "backups/restic"
    if repository.exists() and any(repository.iterdir()):
        raise RuntimeError("refusing to initialize a nonempty repository")
    password_file = password_file.resolve()
    password_file.parent.mkdir(parents=True, exist_ok=True)
    # Never read or print the key; never overwrite an existing one.
    if not password_file.exists():
        fd = os.open(password_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as out:
            out.write(secrets.token_urlsafe(48) + "\n")
    config = {"backend": "restic", "repository": str(repository),
              "passwordFile": str(password_file), "compression": "max", "retain": 1}
    repository.mkdir(mode=0o700, parents=True, exist_ok=True)
    restic_run(config, "init", "--repository-version", "2")
    _atomic_json(config_path, config)
    return config


def require_backup_unpinned(root: pathlib.Path) -> None:
    """Never replace a migration's only pre-conversion restore point."""
    if (root / "state/backup-hold.json").exists():
        raise RuntimeError("backup restore point is pinned; complete or roll back migration before replacing it")


def backup_restic(root: pathlib.Path, manifest: dict, *, label: str,
                  copy_dir: pathlib.Path | None = None) -> pathlib.Path:
    require_backup_unpinned(root)
    if copy_dir is not None:
        raise RuntimeError("Restic off-host backups require repository replication, not receipt copying")
    ensure_layout(root)
    identity = require_world_identity(root, manifest)
    config = load_json(root / "state/backup-config.json")
    require_free_space(root, 0, "incremental backup")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    meta = {"schemaVersion": 1, "createdUtc": stamp,
            "packVersion": manifest["packVersion"],
            "protocolVersion": manifest["protocolVersion"], "world": identity}
    _atomic_json(root / "persistent/.drewcraft-backup-metadata.json", meta)
    output = restic_run(config, "backup", "--json", "--tag", "drewcraft",
                        "--tag", label, "persistent", cwd=root)
    summaries = [item for line in output.splitlines()
                 if (item := json.loads(line)).get("message_type") == "summary"]
    if len(summaries) != 1 or not re.fullmatch(r"[0-9a-f]{8,64}", summaries[0].get("snapshot_id", "")):
        raise RuntimeError("Restic did not confirm a completed snapshot")
    # Never activate a release after a partial backup (exit 3 raises above).
    restic_run(config, "check")
    receipt = root / "backups" / f"{stamp}.restic.json"
    _atomic_json(receipt, {**meta, **config, "snapshotId": summaries[0]["snapshot_id"],
                           "summary": summaries[0]})
    # This dedicated repository has one global restore point, regardless of
    # label/host. Never discard the old point before a new snapshot passes check.
    restic_run(config, "forget", "--tag", "drewcraft", "--group-by", "",
               "--keep-last", "1", "--prune")
    remaining = json.loads(restic_run(config, "snapshots", "--json", "--tag", "drewcraft"))
    if len(remaining) != 1 or not remaining[0]["id"].startswith(summaries[0]["snapshot_id"]):
        raise RuntimeError("single-backup retention did not preserve the new snapshot")
    for stale in (root / "backups").glob("*.restic.json"):
        if stale != receipt and load_json(stale).get("repository") == config["repository"]:
            stale.unlink()
    return receipt


def restore_restic(receipt: pathlib.Path, target_root: pathlib.Path) -> pathlib.Path:
    info = load_json(receipt)
    snapshot = info.get("snapshotId", "")
    if not re.fullmatch(r"[0-9a-f]{8,64}", snapshot):
        raise RuntimeError("invalid Restic snapshot ID")
    if target_root.is_symlink() or (target_root.exists() and any(target_root.iterdir())):
        raise RuntimeError("Restic restore target must be empty and not a symlink")
    target_root.mkdir(parents=True, exist_ok=True)
    restic_run(info, "restore", snapshot, "--target", str(target_root.resolve()), "--verify")
    target = target_root / "persistent"
    identity = read_world_identity(target_root)
    if identity != info["world"]:
        raise RuntimeError("restored world identity differs from snapshot receipt")
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
                       start_command: str | None = None, health_command: str | None = None,
                       backup_retain: int = 1, backup_copy_dir: pathlib.Path | None = None) -> dict:
    require_storage_compatibility(root, manifest)
    require_world_identity(root, manifest)
    release = stage_release(root, manifest)
    write_health(root, "updating", manifest)
    run_cmd(stop_command)
    try:
        archive = backup(root, manifest, label="pre-update", retain=backup_retain, copy_dir=backup_copy_dir)
    except Exception:
        run_cmd(start_command)
        write_health(root, "ready", manifest, "update aborted because the stopped-world backup failed")
        raise
    previous = activate(root, release, manifest)
    try:
        run_cmd(start_command)
        run_cmd(health_command)
    except Exception:
        previous_manifest = rollback_application(root, previous)
        if previous_manifest is not None:
            write_health(
                root,
                "ready",
                previous_manifest,
                "rolled back failed application release; persistent world was not rolled back",
            )
            if start_command:
                run_cmd(start_command)
        else:
            write_health(root, "failed", manifest, "first application rollout failed; no prior release exists")
        raise
    write_health(root, "ready", manifest)
    return {"release": str(release), "backup": str(archive), "previous": str(previous) if previous else None}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="/srv/drewcraft")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("backup-init"); init.add_argument("--password-file", default="/etc/drewcraft/restic-password")
    s = sub.add_parser("stage"); s.add_argument("manifest")
    a = sub.add_parser("activate"); a.add_argument("manifest")
    b = sub.add_parser("backup"); b.add_argument("manifest"); b.add_argument("--label", default="manual"); b.add_argument("--retain", type=int, default=1); b.add_argument("--copy-dir")
    r = sub.add_parser("restore"); r.add_argument("archive"); r.add_argument("--target-root", required=True)
    u = sub.add_parser("update"); u.add_argument("manifest"); u.add_argument("--stop-command"); u.add_argument("--start-command"); u.add_argument("--health-command"); u.add_argument("--backup-retain", type=int, default=1); u.add_argument("--backup-copy-dir")
    args = p.parse_args()
    root = pathlib.Path(args.root)
    if args.command == "backup-init":
        print(json.dumps(init_restic(root, pathlib.Path(args.password_file))))
        return 0
    if args.command == "restore":
        print(restore_backup(pathlib.Path(args.archive), pathlib.Path(args.target_root)))
        return 0
    manifest = validate_manifest(load_json(args.manifest))
    if args.command == "stage": print(stage_release(root, manifest))
    elif args.command == "activate": print(activate(root, stage_release(root, manifest), manifest))
    elif args.command == "backup": print(backup(root, manifest, label=args.label, retain=args.retain,
                                                  copy_dir=pathlib.Path(args.copy_dir) if args.copy_dir else None))
    elif args.command == "update":
        print(json.dumps(update_transaction(root, manifest, stop_command=args.stop_command,
                                            start_command=args.start_command, health_command=args.health_command,
                                            backup_retain=args.backup_retain,
                                            backup_copy_dir=pathlib.Path(args.backup_copy_dir) if args.backup_copy_dir else None), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
