#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
import time
import zipfile
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


def source_build_specs(root: Path) -> dict:
    path = root / "pack/manifest/source_builds.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("source_builds") or {}


def verify_source_build(cid: str, src: Path, evidence: dict, spec: dict) -> dict:
    """Verify a source-built jar by immutable inputs/content, not ZIP metadata timestamps.

    Gradle archive timestamps can make two jars from the same source differ at the raw-byte
    level. For source builds we therefore verify the exact source ref/build spec and a pinned
    embedded model manifest. The raw jar SHA-256 is still recorded for the produced artifact
    and becomes the binary release lock when a specific built jar is published.
    """
    if evidence.get("source_repository") != (spec.get("source") or {}).get("repository"):
        raise pack.PackError(f"{cid}: source repository evidence drift")
    if evidence.get("source_ref") != (spec.get("source") or {}).get("ref"):
        raise pack.PackError(f"{cid}: source ref evidence drift")
    expected_filename = evidence.get("filename")
    if expected_filename and src.name != expected_filename:
        raise pack.PackError(f"{cid}: source-build filename mismatch expected={expected_filename} got={src.name}")

    expected_manifest_hash = evidence.get("model_assets_manifest_sha256")
    if not isinstance(expected_manifest_hash, str) or len(expected_manifest_hash) != 64:
        raise pack.PackError(f"{cid}: missing model-assets manifest hash evidence")

    try:
        with zipfile.ZipFile(src) as jar:
            matches = [name for name in jar.namelist() if name.endswith("model-assets-manifest.json")]
            if len(matches) != 1:
                raise pack.PackError(f"{cid}: expected one embedded model-assets-manifest.json, found {matches}")
            raw_manifest = jar.read(matches[0])
    except zipfile.BadZipFile as exc:
        raise pack.PackError(f"{cid}: source-built artifact is not a valid jar") from exc

    manifest_hash = hashlib.sha256(raw_manifest).hexdigest()
    if manifest_hash.lower() != expected_manifest_hash.lower():
        raise pack.PackError(
            f"{cid}: embedded model manifest mismatch expected={expected_manifest_hash} got={manifest_hash}"
        )
    model_manifest = json.loads(raw_manifest.decode("utf-8"))
    model_spec = spec.get("model_assets") or {}
    if model_manifest.get("repositorySlug") != model_spec.get("repository"):
        raise pack.PackError(f"{cid}: embedded model repository drift")
    if model_manifest.get("revision") != model_spec.get("revision"):
        raise pack.PackError(f"{cid}: embedded model revision drift")
    if set((model_manifest.get("assets") or {}).keys()) != set(model_spec.get("required_files") or []):
        raise pack.PackError(f"{cid}: embedded model asset set drift")

    return {
        "raw_sha256": pack.sha256(src),
        "model_assets_manifest_sha256": manifest_hash,
        "verification_mode": "source_ref_plus_embedded_manifest",
    }


def fetch_providers_with_retries(provider_plan: dict, hydrated: dict, cache: Path, attempts: int = 4) -> dict:
    last = provider_plan
    for attempt in range(1, attempts + 1):
        last = pack.fetch(copy.deepcopy(provider_plan), cache, hydrated)
        failures = last.get("fetch_failures") or []
        if not failures:
            return last
        if attempt < attempts:
            print(f"provider fetch attempt {attempt}/{attempts} failed for {failures}; retrying")
            time.sleep(2 ** attempt)
    return last


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
    source_specs = source_build_specs(root)

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
        fetched = fetch_providers_with_retries(provider_plan, hydrated, Path(temp))
        if fetched.get("fetch_failures"):
            details = {
                d["id"]: (d.get("fetch") or {}).get("reason")
                for d in fetched.get("dependencies") or []
                if d["id"] in fetched["fetch_failures"]
            }
            raise pack.PackError(f"provider fetch failures after retries: {details}")
        by_id = {d["id"]: d for d in fetched["dependencies"]}

        for dep in plan["dependencies"]:
            if dep["id"] in by_id:
                dep["fetch"] = by_id[dep["id"]]["fetch"]

        source_verification = {}
        for dep in source_deps:
            cid = dep["id"]
            src = source_paths.get(cid)
            if src is None:
                raise pack.PackError(f"{cid}: source-built artifact path is required")
            if not src.is_file():
                raise pack.PackError(f"{cid}: source-built artifact not found: {src}")
            evidence = source_hashes.get(cid) or {}
            spec = source_specs.get(cid) or {}
            if not evidence or not spec:
                raise pack.PackError(f"{cid}: source build evidence/spec is missing")
            verification = verify_source_build(cid, src, evidence, spec)
            digest = verification["raw_sha256"]
            source_verification[cid] = verification
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
            pack.build(plan, output, target, root)
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
            "source_verification": source_verification,
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
