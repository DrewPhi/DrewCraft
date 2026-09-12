#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import drewcraft_pack as pack


def main() -> int:
    ap = argparse.ArgumentParser(description="Acquire provider-backed profile artifacts and emit a SHA-256 report without publishing jars.")
    ap.add_argument("--profile", action="append", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    profiles_doc = pack.load_yaml(root / "pack/manifest/profiles.yaml")
    catalog = pack.collect_catalog(root, profiles_doc)
    resolved = pack.resolve(args.profile, profiles_doc, catalog)
    plan = pack.make_plan(resolved, catalog)
    hydrated = pack.hydrate(json.loads(json.dumps(plan)))

    with tempfile.TemporaryDirectory(prefix="drewcraft-hash-") as td:
        result = pack.fetch(plan, Path(td), hydrated)

        hard_failures = []
        source_builds = []
        report_entries = []
        for dep in result["dependencies"]:
            provider = (dep.get("artifact") or {}).get("provider")
            fetched = dep.get("fetch") or {}
            if provider == "source_build":
                source_builds.append(dep["id"])
                continue
            if fetched.get("status") != "ok":
                hard_failures.append({"id": dep["id"], "reason": fetched.get("reason", "unknown")})
                continue
            report_entries.append({
                "id": dep["id"],
                "provider": provider,
                "project_id": (dep.get("artifact") or {}).get("project_id"),
                "file_id": (dep.get("artifact") or {}).get("file_id"),
                "version_id": (dep.get("artifact") or {}).get("version_id"),
                "filename": fetched["filename"],
                "sha256": fetched["sha256"],
                "size": fetched["size"],
                "source_url": fetched["source_url"],
            })

    report = {
        "schema_version": 1,
        "profiles": result["profiles"],
        "provider_artifact_count": len(report_entries),
        "source_builds_pending": source_builds,
        "hard_failures": hard_failures,
        "artifacts": sorted(report_entries, key=lambda x: x["id"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"hashed={len(report_entries)} source_builds_pending={len(source_builds)} hard_failures={len(hard_failures)}")
    for failure in hard_failures:
        print(f"FAIL {failure['id']}: {failure['reason']}")
    return 2 if hard_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
