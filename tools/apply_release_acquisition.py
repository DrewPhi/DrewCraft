#!/usr/bin/env python3
"""Apply original-provider acquisition URLs to a DrewCraft release manifest.

Provider artifact identity is already hash-locked in candidate_hashes.yaml. This
step matches release files by exact SHA-256 and changes only the download URL;
DrewCraft-built/source-built/server-runtime content remains on the DrewCraft
release base supplied by build_release_manifest.py.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import urllib.request

import yaml

from release_contract import canonical_json_bytes, validate_manifest


def curseforge_url(item: dict) -> str:
    return f"https://www.curseforge.com/api/v1/mods/{int(item['project_id'])}/files/{int(item['file_id'])}/download"


def resolve_modrinth_url(item: dict) -> str:
    version_id = item["version_id"]
    request = urllib.request.Request(
        f"https://api.modrinth.com/v2/version/{version_id}",
        headers={"User-Agent": "DrewCraft-ReleaseAcquisition/1"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    filename = item.get("filename")
    matches = [file for file in payload.get("files", []) if file.get("filename") == filename]
    if len(matches) != 1 or not matches[0].get("url"):
        raise RuntimeError(f"Modrinth version {version_id} did not resolve exact file {filename!r}")
    return matches[0]["url"]


def provider_urls(evidence: dict, *, modrinth_resolver=resolve_modrinth_url) -> dict[str, dict]:
    if evidence.get("schema_version") != 1:
        raise RuntimeError("unsupported candidate-hash evidence schema")
    by_sha: dict[str, dict] = {}
    for artifact_id, item in (evidence.get("artifacts") or {}).items():
        sha = str(item.get("sha256", "")).lower()
        if len(sha) != 64:
            raise RuntimeError(f"{artifact_id}: invalid locked SHA-256")
        provider = item.get("provider")
        if provider == "curseforge":
            url = curseforge_url(item)
            origin = {
                "type": "provider",
                "provider": "curseforge",
                "projectId": item["project_id"],
                "fileId": item["file_id"],
            }
        elif provider == "modrinth":
            url = modrinth_resolver(item)
            origin = {
                "type": "provider",
                "provider": "modrinth",
                "projectId": item["project_id"],
                "versionId": item["version_id"],
            }
        else:
            # Source-built and repository-owned artifacts are intentionally not
            # inferred here; their release URL remains the DrewCraft base URL.
            continue
        if sha in by_sha:
            raise RuntimeError(f"duplicate locked provider SHA-256: {sha}")
        by_sha[sha] = {"url": url, "origin": origin, "artifactId": artifact_id}
    return by_sha


def apply(manifest: dict, evidence: dict, *, modrinth_resolver=resolve_modrinth_url) -> dict:
    manifest = validate_manifest(manifest)
    lookup = provider_urls(evidence, modrinth_resolver=modrinth_resolver)
    matched = set()
    for entry in manifest["files"]:
        source = lookup.get(entry["sha256"].lower())
        if source is None:
            entry.setdefault("origin", {"type": "drewcraft_release"})
            continue
        entry["url"] = source["url"]
        entry["origin"] = source["origin"]
        entry["artifactId"] = source["artifactId"]
        matched.add(entry["sha256"].lower())
    manifest["acquisitionPolicy"] = {
        "providerFiles": len(matched),
        "drewcraftReleaseFiles": sum(1 for entry in manifest["files"] if entry.get("origin", {}).get("type") == "drewcraft_release"),
        "rule": "Exact locked provider artifacts are fetched from their original provider when available; DrewCraft/source-built/runtime files use the immutable DrewCraft release base.",
    }
    return validate_manifest(manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--hash-evidence", default="pack/manifest/candidate_hashes.yaml")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    manifest = json.loads(pathlib.Path(args.manifest).read_text("utf-8"))
    evidence = yaml.safe_load(pathlib.Path(args.hash_evidence).read_text("utf-8"))
    result = apply(manifest, evidence)
    pathlib.Path(args.output).write_bytes(canonical_json_bytes(result))
    print(json.dumps(result["acquisitionPolicy"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
