#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path

import yaml

import drewcraft_pack as pack


def load_hash_evidence(root: Path) -> dict:
    path = root / "pack/manifest/candidate_hashes.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("artifacts"), dict):
        raise pack.PackError(f"invalid candidate hash evidence: {path}")
    return data


def verify_identity(dep: dict, evidence: dict) -> None:
    a = dep["artifact"]
    if evidence.get("provider") != a.get("provider"):
        raise pack.PackError(f"{dep['id']}: hash evidence provider identity mismatch")
    provider = a.get("provider")
    if provider == "curseforge":
        if evidence.get("project_id") != a.get("project_id") or evidence.get("file_id") != a.get("file_id"):
            raise pack.PackError(f"{dep['id']}: CurseForge project/file identity drift")
    elif provider == "modrinth":
        if evidence.get("project_id") != a.get("project_id") or evidence.get("version_id") != a.get("version_id"):
            raise pack.PackError(f"{dep['id']}: Modrinth project/version identity drift")
    if evidence.get("filename") and a.get("filename") and evidence["filename"] != a["filename"]:
        raise pack.PackError(f"{dep['id']}: filename identity drift")
    digest = evidence.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise pack.PackError(f"{dep['id']}: invalid or missing SHA-256 evidence")


def parse_source_args(values: list[str]) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for raw in values:
        if "=" not in raw:
            raise pack.PackError(f"--source-artifact must be id=path, got {raw!r}")
        cid, value = raw.split("=", 1)
        out[cid] = Path(value).resolve()
    return out


def source_expected_hashes(root: Path) -> dict:
    path = root / "pack/manifest/source_build_hashes.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("artifacts") or {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Build and verify a DrewCraft profile from pinned provider hashes plus exact source-built artifacts.")
    ap.add_argument("--profile", action="append", required=True)
    ap.add_argument("--source-artifact", action="append", default=[], help="id=/absolute/or/relative/path.jar")
    ap.add_argument("--output-dir", type=Path, default=Path("build/verified-pack"))
    ap.add_argument("--evidence-output", type=Path, default=Path("build/verified-pack-evidence.json"))
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    profiles_doc = pack.load_yaml(root / "pack/manifest/profiles.yaml")
    catalog = pack.collect_catalog(root, profiles_doc)
    resolved = pack.resolve(args.profile, profiles_doc, catalog)
    plan = pack.make_plan(resolved, catalog)
    hash_evidence = load_hash_evidence(root)
    recorded = hash_evidence["artifacts"]
    source_paths = parse_source_args(args.source_artifact)
    source_hashes = source_expected_hashes(root)

    provider_plan = copy.deepcopy(plan)
    provider_plan["dependencies"] = []
    source_deps = []
    for dep in plan["dependencies"]:
        if dep["artifact"].get("provider") == "source_build":
            source_deps.append(dep)
            continue
        evidence = recorded.get(dep["id"])
        if not evidence:
            raise pack.PackError(f"{dep['id']}: no committed candidate hash evidence")
        verify_identity(dep, evidence)
        dep["artifact"]["sha256"] = evidence["sha256"]
        provider_plan["dependencies"].append(copy.deepcopy(dep))

    hydrated = pack.hydrate(copy.deepcopy(provider_plan))
    with tempfile.TemporaryDirectory(prefix="drewcraft-verified-") as temp:
        fetched = pack.fetch(provider_plan, Path(temp), hydrated)
        if fetched.get("fetch_failures"):
            raise pack.PackError(f"provider fetch failures: {fetched['fetch_failures']}")
        by_id = {d["id"]: d for d in fetched["dependencies"]}

        for dep in plan["dependencies"]:
            if dep["id"] in by_id:
                dep["fetch"] = by_id[dep["id"]]["fetch"]

        for dep in source_deps:
            cid = dep["id"]
            src = source_paths.get(cid)
            if src is None:
                raise pack.PackError(f"{cid}: source-built artifact path is required")
            if not src.is_file():
                raise pack.PackError(f"{cid}: source-built artifact not found: {src}")
            digest = pack.sha256(src)
            expected = (source_hashes.get(cid) or {}).get("sha256")
            if not expected:
                raise pack.PackError(f"{cid}: no committed source-build SHA-256 evidence")
            if digest.lower() != str(expected).lower():
                raise pack.PackError(f"{cid}: source-build hash mismatch expected={expected} got={digest}")
            expected_filename = (source_hashes.get(cid) or {}).get("filename")
            if expected_filename and src.name != expected_filename:
                raise pack.PackError(f"{cid}: source-build filename mismatch expected={expected_filename} got={src.name}")
            dep["fetch"] = {
                "status": "ok",
                "path": str(src),
                "filename": src.name,
                "sha256": digest,
                "size": src.stat().st_size,
                "source_url": None,
            }

        output = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
        for target in ("client", "server"):
            pack.build(plan, output, target)
            pack.verify(output / target)

        layouts = {}
        for target in ("client", "server"):
            layout_path = output / target / "drewcraft-layout.json"
            layouts[target] = json.loads(layout_path.read_text(encoding="utf-8"))

        evidence = {
            "schema_version": 1,
            "profiles": plan["profiles"],
            "dependency_count": len(plan["dependencies"]),
            "provider_hash_evidence_run": hash_evidence.get("evidence"),
            "client_file_count": len(layouts["client"]["files"]),
            "server_file_count": len(layouts["server"]["files"]),
            "layouts": layouts,
        }
        evidence_path = args.evidence_output if args.evidence_output.is_absolute() else root / args.evidence_output
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"verified profile={','.join(plan['profiles'])} deps={len(plan['dependencies'])} client={evidence['client_file_count']} server={evidence['server_file_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
