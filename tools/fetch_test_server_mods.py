#!/usr/bin/env python3
"""Fetch playtest_01 mod jars from official CDNs (no API key) and verify SHA-256.

Sources:
- Modrinth CDN for modrinth entries (version_id + filename).
- CurseForge edge CDN for curseforge entries (file_id + filename).
- Expected hashes from pack/manifest/candidate_hashes.yaml and
  pack/manifest/mob_structure_candidates.yaml.

Writes verified jars to build/test-server-mods/ plus fetch-report.json.
Terrain Diffusion Plus (source build) is excluded; it builds on the server.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import urllib.parse
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "test-server-mods"


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def edge_url(file_id: int, filename: str) -> str:
    s = str(file_id)
    return f"https://edge.forgecdn.net/files/{s[:4]}/{s[4:]}/{urllib.parse.quote(filename)}"


def modrinth_url(project_id: str, version_id: str, filename: str) -> str:
    return f"https://cdn.modrinth.com/data/{project_id}/versions/{version_id}/{filename}"


def collect_expected() -> dict[str, dict]:
    """id -> {filename, sha256, url} from manifests."""
    out: dict[str, dict] = {}
    hashes = yaml.safe_load((ROOT / "pack/manifest/candidate_hashes.yaml").read_text(encoding="utf-8"))
    for cid, art in (hashes.get("artifacts") or {}).items():
        provider = art.get("provider")
        if provider == "modrinth":
            url = modrinth_url(art["project_id"], art["version_id"], art["filename"])
        elif provider == "curseforge":
            url = edge_url(art["file_id"], art["filename"])
        else:
            continue
        out[str(cid)] = {"filename": art["filename"], "sha256": art["sha256"], "url": url}

    mob = yaml.safe_load((ROOT / "pack/manifest/mob_structure_candidates.yaml").read_text(encoding="utf-8"))
    combat = yaml.safe_load((ROOT / "pack/manifest/create_combat_mobility_candidates.yaml").read_text(encoding="utf-8"))

    def walk(node, pin_without_hash: bool = False):
        if isinstance(node, dict):
            if "id" in node and isinstance(node["id"], str) and "filename" in node:
                cid = node["id"]
                if cid not in out:
                    prov = node.get("provider")
                    filename = node["filename"]
                    if isinstance(prov, dict):
                        file_id = prov.get("file_id")
                        if node.get("sha256"):
                            out[cid] = {"filename": filename, "sha256": node["sha256"],
                                        "url": edge_url(file_id, filename) if file_id else None}
                        elif pin_without_hash and file_id:
                            out[cid] = {"filename": filename, "sha256": None,
                                        "url": edge_url(file_id, filename), "pin_at_fetch": True}
                    else:
                        if node.get("sha256"):
                            if prov == "modrinth":
                                url = modrinth_url(node["project_id"], node["version_id"], filename)
                            elif prov == "curseforge" and node.get("file_id"):
                                url = edge_url(node["file_id"], filename)
                            else:
                                return
                            out[cid] = {"filename": filename, "sha256": node["sha256"], "url": url}
            for key, value in node.items():
                # Keyed-mapping style (create_combat file: components:<id>: {...},
                # filename nested under provider).
                if (isinstance(key, str) and isinstance(value, dict)
                        and ("display_name" in value or "kind" in value) and key not in out):
                    prov = value.get("provider")
                    filename = value.get("filename") or (prov.get("filename") if isinstance(prov, dict) else None)
                    file_id = prov.get("file_id") if isinstance(prov, dict) else value.get("file_id")
                    if filename and file_id and pin_without_hash:
                        out[key] = {"filename": filename, "sha256": value.get("sha256") or None,
                                    "url": edge_url(file_id, filename), "pin_at_fetch": True}
                walk(value, pin_without_hash)
        elif isinstance(node, list):
            for v in node:
                walk(v, pin_without_hash)

    walk(mob)
    walk(combat, pin_without_hash=True)
    return out


def download(url: str, dest: pathlib.Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "DrewCraft-TestFetch/1"})
    with urllib.request.urlopen(req, timeout=300) as resp, dest.open("wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)


def main() -> int:
    plan = json.loads((ROOT / "build/playtest01-plan.json").read_text(encoding="utf-8"))
    expected = collect_expected()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"ok": [], "failed": [], "skipped": []}
    for dep in plan["dependencies"]:
        cid = dep["id"]
        if cid == "terrain_diffusion_plus":
            report["skipped"].append({"id": cid, "reason": "source build on server"})
            continue
        exp = expected.get(cid)
        if not exp:
            report["failed"].append({"id": cid, "reason": "no expected hash/url in manifests"})
            continue
        dest = OUT / exp["filename"]
        if exp.get("sha256") and dest.is_file() and sha256(dest) == exp["sha256"]:
            report["ok"].append({"id": cid, "cached": True})
            continue
        if not exp.get("url"):
            report["failed"].append({"id": cid, "reason": "no download URL"})
            continue
        try:
            download(exp["url"], dest)
        except Exception as exc:  # noqa: BLE001
            report["failed"].append({"id": cid, "reason": f"download: {exc}"})
            continue
        got = sha256(dest)
        if exp.get("sha256"):
            if got != exp["sha256"]:
                report["failed"].append({"id": cid, "reason": f"hash mismatch got={got}"})
                dest.unlink(missing_ok=True)
            else:
                report["ok"].append({"id": cid, "cached": False})
        else:
            # Test-only pin: file ID was frozen in the manifest; record the
            # observed hash as the test lock (NOT production evidence).
            report["ok"].append({"id": cid, "cached": False, "pinned_sha256": got, "test_only": True})
    (OUT / "fetch-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"ok={len(report['ok'])} failed={len(report['failed'])} skipped={len(report['skipped'])}")
    for f in report["failed"]:
        print("FAILED:", f)
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
