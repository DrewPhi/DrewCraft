#!/usr/bin/env python3
"""Build a DrewCraft release-manifest.json from an assembled release layout."""
from __future__ import annotations

import argparse
import json
import pathlib

from release_contract import build_manifest_from_layout, write_manifest


def runtime_from_lock(lock: dict) -> dict:
    if lock.get("schemaVersion") != 1:
        raise ValueError("unsupported runtime lock schema")
    result = {}
    for platform in ("windows-x86_64", "macos-arm64"):
        spec = lock.get("platforms", {}).get(platform)
        if not spec or "java" not in spec or "prism" not in spec:
            raise ValueError(f"runtime lock missing {platform}")
        result[platform] = {"java": spec["java"], "prism": spec["prism"]}
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--layout", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--base-url", required=True)
    p.add_argument("--pack-version", required=True)
    p.add_argument("--protocol-version", type=int, required=True)
    p.add_argument("--world-id", required=True)
    p.add_argument("--world-revision", type=int, required=True)
    p.add_argument("--generation-pack-version", required=True)
    p.add_argument("--channel", default="stable")
    p.add_argument("--minecraft-version", default="1.21.1")
    p.add_argument("--neoforge-version", default="21.1.250")
    p.add_argument("--minimum-launcher-version", default="0.1.0")
    p.add_argument("--runtime-lock", default="launcher/runtime-lock.json")
    p.add_argument("--server-address")
    p.add_argument("--health-url")
    args = p.parse_args()

    lock = json.loads(pathlib.Path(args.runtime_lock).read_text("utf-8"))
    server = {}
    if args.server_address:
        server["address"] = args.server_address
    if args.health_url:
        server["healthUrl"] = args.health_url
    manifest = build_manifest_from_layout(
        args.layout,
        pack_version=args.pack_version,
        channel=args.channel,
        protocol_version=args.protocol_version,
        minecraft_version=args.minecraft_version,
        loader_id="neoforge",
        loader_version=args.neoforge_version,
        minimum_launcher_version=args.minimum_launcher_version,
        world_id=args.world_id,
        world_revision=args.world_revision,
        generation_pack_version=args.generation_pack_version,
        base_url=args.base_url,
        runtime=runtime_from_lock(lock),
        server=server or None,
    )
    digest = write_manifest(args.output, manifest)
    print(json.dumps({"packVersion": manifest["packVersion"], "sha256": digest, "files": len(manifest["files"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
