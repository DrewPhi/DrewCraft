#!/usr/bin/env python3
"""DrewCraft immutable release manifest builder/verifier.

The same manifest is consumed by the friend-facing launcher and the production
server deployer. Only stdlib is used so the verifier can run on a clean host.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import urllib.parse
import urllib.request

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SIDES = {"common", "client", "server"}


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: os.PathLike[str] | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_rel(path: str) -> str:
    normalized = pathlib.PurePosixPath(path)
    if normalized.is_absolute() or ".." in normalized.parts or "." in normalized.parts or not normalized.parts:
        raise ValueError(f"unsafe managed path: {path!r}")
    return normalized.as_posix()


def validate_manifest(manifest: dict) -> dict:
    required = {
        "schemaVersion", "packVersion", "channel", "protocolVersion",
        "minecraftVersion", "loader", "java", "minimumLauncherVersion",
        "world", "files",
    }
    missing = required - set(manifest)
    if missing:
        raise ValueError(f"manifest missing keys: {sorted(missing)}")
    if manifest["schemaVersion"] != 1:
        raise ValueError("unsupported release manifest schema")
    if not isinstance(manifest["protocolVersion"], int) or manifest["protocolVersion"] < 1:
        raise ValueError("protocolVersion must be a positive integer")
    if manifest["java"].get("major") != 21:
        raise ValueError("DrewCraft V1 release manifest must require Java 21")
    if not manifest["packVersion"]:
        raise ValueError("packVersion must not be blank")
    world = manifest["world"]
    for key in ("worldId", "worldRevision", "generationPackVersion"):
        if key not in world:
            raise ValueError(f"world metadata missing {key}")

    seen = set()
    for entry in manifest["files"]:
        side = entry.get("side")
        if side not in SIDES:
            raise ValueError(f"invalid side: {side!r}")
        path = _safe_rel(entry.get("path", ""))
        key = (side, path)
        if key in seen:
            raise ValueError(f"duplicate release entry: {side}:{path}")
        seen.add(key)
        sha = str(entry.get("sha256", "")).lower()
        if not SHA256_RE.match(sha):
            raise ValueError(f"invalid SHA-256 for {side}:{path}")
        size = entry.get("size")
        if not isinstance(size, int) or size < 0:
            raise ValueError(f"invalid size for {side}:{path}")
        url = entry.get("url")
        if not isinstance(url, str) or not url:
            raise ValueError(f"missing URL for {side}:{path}")
        if entry.get("managed", True) is not True:
            raise ValueError("V1 release files are managed; user data must be outside release trees")
    return manifest


def _entry_url(base_url: str, pack_version: str, side: str, rel: str) -> str:
    parts = [urllib.parse.quote(part) for part in rel.split("/")]
    return f"{base_url.rstrip('/')}/{urllib.parse.quote(pack_version)}/{side}/{'/'.join(parts)}"


def build_manifest_from_layout(
    layout_root: os.PathLike[str] | str,
    *,
    pack_version: str,
    channel: str,
    protocol_version: int,
    minecraft_version: str,
    loader_id: str,
    loader_version: str,
    minimum_launcher_version: str,
    world_id: str,
    world_revision: int,
    generation_pack_version: str,
    base_url: str,
    runtime: dict | None = None,
    server: dict | None = None,
) -> dict:
    root = pathlib.Path(layout_root)
    files: list[dict] = []
    seen: set[str] = set()
    for side in ("common", "client", "server"):
        side_root = root / side
        if not side_root.exists():
            continue
        for path in sorted(p for p in side_root.rglob("*") if p.is_file()):
            rel = path.relative_to(side_root).as_posix()
            if pathlib.PurePosixPath(rel).name == "drewcraft-layout.json":
                # Builder metadata, not managed game content: each pack tree
                # carries its own layout file, and listing both would create a
                # duplicate managed path that launchers must reject.
                continue
            if rel in seen:
                raise RuntimeError(f"duplicate managed path in release layout: {rel}")
            seen.add(rel)
            files.append({
                "path": _safe_rel(rel),
                "side": side,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
                "url": _entry_url(base_url, pack_version, side, rel),
                "managed": True,
            })
    manifest = {
        "schemaVersion": 1,
        "packVersion": pack_version,
        "channel": channel,
        "protocolVersion": protocol_version,
        "minecraftVersion": minecraft_version,
        "loader": {"id": loader_id, "version": loader_version},
        "java": {"major": 21},
        "minimumLauncherVersion": minimum_launcher_version,
        "world": {
            "worldId": world_id,
            "worldRevision": world_revision,
            "generationPackVersion": generation_pack_version,
        },
        "files": files,
    }
    if runtime:
        manifest["runtime"] = runtime
    if server:
        manifest["server"] = server
    return validate_manifest(manifest)


def manifest_sha256(manifest: dict) -> str:
    validate_manifest(manifest)
    return sha256_bytes(canonical_json_bytes(manifest))


def write_manifest(path: os.PathLike[str] | str, manifest: dict) -> str:
    payload = canonical_json_bytes(validate_manifest(manifest))
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(path).write_bytes(payload)
    return sha256_bytes(payload)


def load_json(source: str | os.PathLike[str]) -> dict:
    s = str(source)
    parsed = urllib.parse.urlparse(s)
    if parsed.scheme in ("http", "https", "file"):
        req = urllib.request.Request(s, headers={"User-Agent": "DrewCraft-Release/1"})
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    return json.loads(pathlib.Path(s).read_text("utf-8"))


def verify_manifest_payload(payload: bytes, expected_sha256: str) -> dict:
    got = sha256_bytes(payload)
    if got.lower() != expected_sha256.lower():
        raise ValueError(f"manifest hash mismatch expected={expected_sha256} got={got}")
    return validate_manifest(json.loads(payload.decode("utf-8")))


def selected_files(manifest: dict, side: str) -> list[dict]:
    if side not in ("client", "server"):
        raise ValueError("side must be client or server")
    validate_manifest(manifest)
    return [entry for entry in manifest["files"] if entry["side"] in ("common", side)]


def verify_tree(root: os.PathLike[str] | str, manifest: dict, side: str) -> list[str]:
    root = pathlib.Path(root)
    failures: list[str] = []
    for entry in selected_files(manifest, side):
        path = root / _safe_rel(entry["path"])
        if not path.is_file():
            failures.append(f"missing:{entry['path']}")
            continue
        if path.stat().st_size != entry["size"]:
            failures.append(f"size:{entry['path']}")
            continue
        if sha256_file(path) != entry["sha256"]:
            failures.append(f"sha256:{entry['path']}")
    return failures


def make_live_pointer(channel: str, manifest_url: str, manifest: dict) -> dict:
    return {
        "schemaVersion": 1,
        "channel": channel,
        "packVersion": manifest["packVersion"],
        "protocolVersion": manifest["protocolVersion"],
        "manifestUrl": manifest_url,
        "manifestSha256": manifest_sha256(manifest),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("manifest")

    verify = sub.add_parser("verify")
    verify.add_argument("manifest")
    verify.add_argument("--root", required=True)
    verify.add_argument("--side", choices=("client", "server"), required=True)

    promote = sub.add_parser("promote")
    promote.add_argument("manifest")
    promote.add_argument("--manifest-url", required=True)
    promote.add_argument("--channel", default="stable")
    promote.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "validate":
        manifest = validate_manifest(load_json(args.manifest))
        print(json.dumps({"ok": True, "packVersion": manifest["packVersion"], "sha256": manifest_sha256(manifest)}))
        return 0
    if args.command == "verify":
        manifest = validate_manifest(load_json(args.manifest))
        failures = verify_tree(args.root, manifest, args.side)
        print(json.dumps({"ok": not failures, "failures": failures}))
        return 0 if not failures else 2
    if args.command == "promote":
        manifest = validate_manifest(load_json(args.manifest))
        pointer = make_live_pointer(args.channel, args.manifest_url, manifest)
        pathlib.Path(args.output).write_bytes(canonical_json_bytes(pointer))
        print(json.dumps(pointer, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
