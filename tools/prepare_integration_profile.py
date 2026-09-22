#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve/hash the V1.1 profile and generate exact MTS/WDA integration artifacts.")
    ap.add_argument("--profile", default="v1_1_integration")
    ap.add_argument("--build-dir", type=Path, default=Path("build/integration-prep"))
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    build = (root / args.build_dir).resolve()
    build.mkdir(parents=True, exist_ok=True)
    report_path = build / "integration-hashes.json"

    run(sys.executable, str(root / "tools/hash_profile.py"), "--profile", args.profile, "--output", str(report_path))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("hard_failures"):
        raise SystemExit(f"provider hash failures: {report['hard_failures']}")

    hash_path = root / "pack/manifest/candidate_hashes.yaml"
    doc = yaml.safe_load(hash_path.read_text(encoding="utf-8")) or {}
    artifacts = doc.setdefault("artifacts", {})
    for a in report["artifacts"]:
        entry = {
            "provider": a["provider"],
            "filename": a["filename"],
            "sha256": a["sha256"],
            "size": a["size"],
        }
        for key in ("project_id", "file_id", "version_id"):
            if a.get(key) is not None:
                entry[key] = a[key]
        artifacts[a["id"]] = entry
    doc["profile"] = args.profile
    doc["evidence"] = {
        "workflow": "integration-prepare.yml",
        "generated_at": "2026-09-20",
        "note": "Exact provider hashes acquired on the isolated 0.1.8-dev-integration branch; no release was published.",
    }
    hash_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    by_id = {x["id"]: x for x in report["artifacts"]}
    inputs = build / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    wanted = {
        "mts_official_pack": inputs / "mts-official-v29.jar",
        "when_dungeons_arise": inputs / "wda.jar",
    }
    for dep_id, out in wanted.items():
        src = by_id[dep_id]["source_url"]
        req = urllib.request.Request(src, headers={"User-Agent": "DrewCraft-integration-prep/0.1.8"})
        with urllib.request.urlopen(req, timeout=180) as response:
            out.write_bytes(response.read())

    overlay = root / "pack/overlays/v1_1_integration"
    datapack = overlay / "datapacks/drewcraft-integration"
    if datapack.exists():
        import shutil
        shutil.rmtree(datapack)
    override = overlay / "config/mtscraftingoverrides.json"
    override.unlink(missing_ok=True)

    run(
        sys.executable,
        str(root / "tools/generate_mts_create_integration.py"),
        "--official-pack", str(wanted["mts_official_pack"]),
        "--wda-jar", str(wanted["when_dungeons_arise"]),
        "--overlay", str(overlay),
        "--report", str(root / "pack/manifest/integration_mts_v29_balance.json"),
    )

    print(
        f"prepared profile={args.profile} provider_artifacts={len(report['artifacts'])} "
        f"source_builds_pending={report.get('source_builds_pending', [])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
