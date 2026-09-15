#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml

DEP_KEYS = (
    "foundation",
    "performance_baseline",
    "performance_libraries",
    "gameplay_components",
    "gameplay_libraries",
    "experimental_performance",
    "create_expansion_components",
    "create_expansion_libraries",
)
CLIENT_SIDES = {"common", "client", "client_and_server_candidate"}
SERVER_SIDES = {
    "common", "server", "server_build_only", "client_and_server_candidate",
    "server_worldbuild_candidate", "server_worldbuild_spike",
}


class PackError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PackError(f"missing manifest: {path}") from exc
    except yaml.YAMLError as exc:
        raise PackError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PackError(f"manifest root must be a mapping: {path}")
    return data


def _artifact_identity(raw: dict[str, Any]) -> tuple:
    # Normalized identity used to tolerate the same upstream artifact being
    # declared in two candidate registries (e.g. radar + combat both declare
    # Create Big Cannons). Only filename/version/provider IDs matter here;
    # notes/license text differences must not block resolution.
    art = artifact({"artifact": {}, **raw}) if "provider" in raw or "artifact" in raw else {}
    provider = raw.get("provider")
    if isinstance(provider, dict):
        provider_type = provider.get("type")
        nested = provider
    else:
        provider_type = provider
        nested = {}
    return (
        str(raw.get("filename") or nested.get("filename") or art.get("filename") or ""),
        str(raw.get("candidate_version") or nested.get("candidate_version") or art.get("candidate_version") or ""),
        str(raw.get("project_id") or nested.get("project_id") or art.get("project_id") or ""),
        str(raw.get("file_id") or nested.get("file_id") or art.get("file_id") or ""),
        str(raw.get("version_id") or nested.get("version_id") or art.get("version_id") or ""),
        str(provider_type or art.get("provider") or ""),
    )


def register(out: dict[str, dict[str, Any]], cid: str, raw: dict[str, Any], registry: str) -> None:
    entry = {"id": cid, "registry": registry, **raw}
    old = out.get(cid)
    if old and old != entry:
        if _artifact_identity(old) == _artifact_identity(entry):
            return
        raise PackError(f"candidate id collision: {cid}")
    out[cid] = entry


def collect_catalog(root: Path, profiles_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    regs = profiles_doc.get("registries") or {}
    if not isinstance(regs, dict):
        raise PackError("profiles.yaml registries must be a mapping")
    for alias, rel in regs.items():
        doc = load_yaml(root / str(rel))
        if alias == "foundation":
            entries = doc.get("upstreams") or {}
            for cid, raw in entries.items():
                register(out, str(cid), raw, str(alias))
        elif alias == "performance":
            for section in ("baseline", "libraries", "experimental"):
                for cid, raw in (doc.get(section) or {}).items():
                    register(out, str(cid), raw, str(alias))
        else:
            def walk(node: Any, key: str | None = None) -> None:
                if isinstance(node, dict):
                    if "id" in node and any(k in node for k in ("provider", "candidate_version", "project_id")):
                        raw = dict(node)
                        cid = str(raw.pop("id"))
                        register(out, cid, raw, str(alias))
                    elif (
                        key
                        and key not in ("provider", "artifact")
                        and any(k in node for k in ("provider", "candidate_version", "project_id"))
                        and any(k in node for k in ("display_name", "kind", "side", "required_for_v1"))
                    ):
                        register(out, key, node, str(alias))
                    for k, v in node.items():
                        walk(v, str(k))
                elif isinstance(node, list):
                    for v in node:
                        walk(v)
            walk(doc)
    return out


def artifact(entry: dict[str, Any]) -> dict[str, Any]:
    nested = dict(entry.get("artifact") or {})
    def pick(name: str):
        return nested.get(name) if nested.get(name) is not None else entry.get(name)
    return {
        "provider": pick("provider"), "project_id": pick("project_id"),
        "file_id": pick("file_id"), "version_id": pick("version_id"),
        "candidate_version": pick("candidate_version"), "filename": pick("filename"),
        "download_url": pick("download_url"), "sha256": pick("sha256"),
        "release_status": pick("release_status"),
    }


def profile_chain(name: str, profiles: dict[str, Any], stack: tuple[str, ...] = ()) -> list[str]:
    if name in stack:
        raise PackError("profile inheritance cycle: " + " -> ".join((*stack, name)))
    raw = profiles.get(name)
    if not isinstance(raw, dict):
        raise PackError(f"unknown profile: {name}")
    result: list[str] = []
    for parent in raw.get("extends") or []:
        result += profile_chain(str(parent), profiles, (*stack, name))
    result.append(name)
    return list(dict.fromkeys(result))


def resolve(names: list[str], profiles_doc: dict[str, Any], catalog: dict[str, dict[str, Any]]) -> dict[str, Any]:
    profiles = profiles_doc.get("profiles") or {}
    expanded: list[str] = []
    for name in names:
        expanded += profile_chain(name, profiles)
    expanded = list(dict.fromkeys(expanded))
    selected = set(expanded)
    for name in expanded:
        for other in profiles[name].get("incompatible_profiles") or []:
            if str(other) in selected:
                raise PackError(f"incompatible profiles selected: {name} and {other}")

    roots: list[str] = []
    policies: list[str] = []
    overlays: list[str] = []
    for name in expanded:
        p = profiles[name]
        for key in DEP_KEYS:
            values = p.get(key) or []
            if not isinstance(values, list):
                raise PackError(f"profile {name}: {key} must be a list")
            roots += [str(x) for x in values]
        for key in ("config_policy", "requirements", "worldgen_policy", "notes"):
            values = p.get(key) or []
            if isinstance(values, list):
                policies += [str(x) for x in values]
        profile_overlays = p.get("overlays") or []
        if not isinstance(profile_overlays, list):
            raise PackError(f"profile {name}: overlays must be a list")
        overlays += [str(x) for x in profile_overlays]

    ordered: list[str] = []
    active: set[str] = set()
    done: set[str] = set()
    def visit(cid: str) -> None:
        if cid in done:
            return
        if cid in active:
            raise PackError(f"dependency cycle involving {cid}")
        if cid not in catalog:
            raise PackError(f"profile references unknown candidate: {cid}")
        active.add(cid)
        deps = catalog[cid].get("required_dependencies") or []
        if not isinstance(deps, list):
            raise PackError(f"{cid}: required_dependencies must be a list")
        for dep in deps:
            visit(str(dep))
        active.remove(cid)
        done.add(cid)
        ordered.append(cid)
    for cid in dict.fromkeys(roots):
        visit(cid)
    return {
        "profiles": expanded,
        "ordered_ids": ordered,
        "policies": policies,
        "overlays": list(dict.fromkeys(overlays)),
    }


def exactness(a: dict[str, Any]) -> list[str]:
    provider = a.get("provider")
    issues: list[str] = []
    if not provider:
        issues.append("provider missing")
    elif provider == "curseforge":
        if a.get("project_id") is None:
            issues.append("CurseForge project_id missing")
        if a.get("file_id") is None:
            issues.append("CurseForge file_id unresolved")
    elif provider == "modrinth":
        if not a.get("version_id") and not a.get("candidate_version"):
            issues.append("Modrinth version unresolved")
    elif provider == "source_build":
        issues.append("source build requires built artifact")
    return issues


def make_plan(resolved: dict[str, Any], catalog: dict[str, dict[str, Any]]) -> dict[str, Any]:
    deps = []
    unresolved = 0
    for cid in resolved["ordered_ids"]:
        entry = catalog[cid]
        a = artifact(entry)
        issues = exactness(a)
        unresolved += bool(issues)
        deps.append({
            "id": cid,
            "display_name": entry.get("display_name") or cid,
            "registry": entry["registry"],
            "side": entry.get("side") or "common",
            "required_dependencies": entry.get("required_dependencies") or [],
            "artifact": a,
            "exact_identity_ready": not issues,
            "identity_issues": issues,
        })
    return {
        "schema_version": 1, "profiles": resolved["profiles"],
        "dependency_count": len(deps), "unresolved_identity_count": unresolved,
        "policies": resolved["policies"], "overlays": resolved.get("overlays") or [],
        "dependencies": deps,
    }


def request_json(url: str, headers: dict[str, str] | None = None) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "DrewCraft-PackResolver/0.1", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise PackError(f"provider request failed: {url}: {exc}") from exc


def hydrate(plan: dict[str, Any]) -> dict[str, Any]:
    key = os.environ.get("CURSEFORGE_API_KEY")
    for dep in plan["dependencies"]:
        a = dep["artifact"]
        provider = a.get("provider")
        if a.get("download_url"):
            dep["hydration"] = {
                "status": "resolved",
                "filename": a.get("filename"),
                "download_url": a.get("download_url"),
                "sha256": a.get("sha256"),
            }
            continue
        try:
            if provider == "curseforge":
                if not key:
                    dep["hydration"] = {"status": "blocked", "reason": "CURSEFORGE_API_KEY not set"}
                    continue
                pid = a.get("project_id")
                if not pid:
                    raise PackError("missing CurseForge project_id")
                headers = {"x-api-key": key}
                if a.get("file_id"):
                    data = request_json(f"https://api.curseforge.com/v1/mods/{pid}/files/{a['file_id']}", headers)["data"]
                else:
                    q = urllib.parse.urlencode({"gameVersion": "1.21.1", "modLoaderType": 6, "pageSize": 50})
                    files = request_json(f"https://api.curseforge.com/v1/mods/{pid}/files?{q}", headers).get("data") or []
                    wanted_file = a.get("filename")
                    wanted_ver = str(a.get("candidate_version") or "")
                    matches = [f for f in files if (wanted_file and f.get("fileName") == wanted_file) or (wanted_ver and wanted_ver in (str(f.get("fileName")) + str(f.get("displayName"))))]
                    if len(matches) != 1:
                        raise PackError(f"expected one CurseForge match, got {len(matches)}")
                    data = matches[0]
                dep["hydration"] = {"status": "resolved", "file_id": data.get("id"), "filename": data.get("fileName"), "download_url": data.get("downloadUrl"), "hashes": data.get("hashes") or []}
            elif provider == "modrinth":
                if a.get("version_id"):
                    data = request_json(f"https://api.modrinth.com/v2/version/{a['version_id']}")
                else:
                    pid = a.get("project_id")
                    q = urllib.parse.urlencode({"loaders": '["neoforge"]', "game_versions": '["1.21.1"]'})
                    versions = request_json(f"https://api.modrinth.com/v2/project/{pid}/version?{q}")
                    wanted = str(a.get("candidate_version") or "")
                    matches = [v for v in versions if v.get("version_number") == wanted]
                    if len(matches) != 1:
                        raise PackError(f"expected one Modrinth match, got {len(matches)}")
                    data = matches[0]
                files = data.get("files") or []
                primary = next((f for f in files if f.get("primary")), files[0] if files else None)
                if not primary:
                    raise PackError("Modrinth version has no file")
                dep["hydration"] = {"status": "resolved", "version_id": data.get("id"), "filename": primary.get("filename"), "download_url": primary.get("url"), "sha256": (primary.get("hashes") or {}).get("sha256")}
            else:
                dep["hydration"] = {"status": "not_supported", "reason": f"provider={provider}"}
        except Exception as exc:
            dep["hydration"] = {"status": "error", "reason": str(exc)}
    return plan


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "DrewCraft-PackResolver/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp, tmp.open("wb") as out:
            shutil.copyfileobj(resp, out)
        tmp.replace(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def fetch(plan: dict[str, Any], cache: Path, hydrated: dict[str, Any] | None) -> dict[str, Any]:
    hmap = {d["id"]: d.get("hydration") or {} for d in (hydrated or {}).get("dependencies", [])}
    failures = []
    for dep in plan["dependencies"]:
        a = dep["artifact"]
        h = hmap.get(dep["id"], {})
        url = h.get("download_url") or a.get("download_url")
        if not url and a.get("provider") == "curseforge" and a.get("project_id") and a.get("file_id"):
            url = f"https://www.curseforge.com/api/v1/mods/{a['project_id']}/files/{a['file_id']}/download"
        filename = h.get("filename") or a.get("filename") or f"{dep['id']}.jar"
        if not url:
            dep["fetch"] = {"status": "blocked", "reason": "no exact download URL"}
            failures.append(dep["id"])
            continue
        dest = cache / filename
        try:
            if not dest.exists():
                download(url, dest)
            digest = sha256(dest)
            expected = h.get("sha256") or a.get("sha256")
            if expected and digest.lower() != str(expected).lower():
                raise PackError(f"hash mismatch expected={expected} got={digest}")
            dep["fetch"] = {"status": "ok", "path": str(dest), "filename": filename, "sha256": digest, "size": dest.stat().st_size, "source_url": url}
        except Exception as exc:
            dep["fetch"] = {"status": "error", "reason": str(exc)}
            failures.append(dep["id"])
    plan["fetch_failures"] = failures
    return plan


def side_allowed(side: str, target: str) -> bool:
    if target == "client":
        return side in CLIENT_SIDES
    if target in {"server", "worldbuild"}:
        return side in SERVER_SIDES
    raise PackError(f"unknown target: {target}")


def build(lock: dict[str, Any], output: Path, target: str, repo_root: Path | None = None) -> None:
    root = output / target
    if root.exists():
        shutil.rmtree(root)
    mods = root / "mods"
    mods.mkdir(parents=True)
    files = []
    for dep in lock.get("dependencies") or []:
        if not side_allowed(str(dep.get("side") or "common"), target):
            continue
        f = dep.get("fetch") or {}
        if f.get("status") != "ok":
            raise PackError(f"{dep['id']}: artifact not fetched")
        src = Path(f["path"])
        dst = mods / f["filename"]
        shutil.copy2(src, dst)
        files.append({"id": dep["id"], "path": dst.relative_to(root).as_posix(), "sha256": f["sha256"]})

    repository = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    for overlay_value in lock.get("overlays") or []:
        overlay = (repository / str(overlay_value)).resolve()
        if repository not in overlay.parents or not overlay.is_dir():
            raise PackError(f"invalid or missing profile overlay: {overlay_value}")
        for src in sorted(p for p in overlay.rglob("*") if p.is_file()):
            rel = src.relative_to(overlay)
            if rel.parts[0] == "mods" or rel.as_posix() == "drewcraft-layout.json":
                raise PackError(f"profile overlay cannot manage reserved path: {rel}")
            dst = root / rel
            if dst.exists():
                raise PackError(f"profile overlays collide at: {rel}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            files.append({
                "id": f"overlay:{overlay_value}",
                "path": rel.as_posix(),
                "sha256": sha256(dst),
            })
    manifest = {"schema_version": 1, "target": target, "profiles": lock.get("profiles") or [], "files": files}
    (root / "drewcraft-layout.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(root: Path) -> None:
    data = json.loads((root / "drewcraft-layout.json").read_text(encoding="utf-8"))
    expected = {f["path"]: f for f in data.get("files") or []}
    actual = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and p.name != "drewcraft-layout.json"
    }
    missing = sorted(set(expected) - actual)
    unexpected = sorted(actual - set(expected))
    bad = [rel for rel, item in expected.items() if (root / rel).exists() and sha256(root / rel) != item["sha256"]]
    if missing or unexpected or bad:
        raise PackError(f"layout verification failed missing={missing} unexpected={unexpected} bad_hash={bad}")


def write_json(data: dict[str, Any], path: Path | None) -> None:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "plan", "hydrate"):
        q = sub.add_parser(name); q.add_argument("--profile", action="append", required=True); q.add_argument("--output", type=Path)
    q = sub.add_parser("fetch"); q.add_argument("--profile", action="append", required=True); q.add_argument("--hydration", type=Path); q.add_argument("--cache-dir", type=Path, default=Path(".cache/drewcraft/artifacts")); q.add_argument("--output", type=Path, required=True)
    q = sub.add_parser("build"); q.add_argument("--lock", type=Path, required=True); q.add_argument("--target", choices=["client", "server", "worldbuild"], required=True); q.add_argument("--output-dir", type=Path, default=Path("build/pack"))
    q = sub.add_parser("verify"); q.add_argument("layout", type=Path)
    args = p.parse_args()
    try:
        if args.cmd == "verify":
            verify(args.layout); print(f"verified {args.layout}"); return 0
        root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[1]
        profiles_doc = load_yaml(root / "pack/manifest/profiles.yaml")
        catalog = collect_catalog(root, profiles_doc)
        resolved = resolve(args.profile, profiles_doc, catalog) if hasattr(args, "profile") else None
        if args.cmd in {"validate", "plan", "hydrate", "fetch"}:
            plan = make_plan(resolved, catalog)
        if args.cmd == "validate":
            plan["validation"] = "ok"; write_json(plan, args.output); return 0
        if args.cmd == "plan":
            write_json(plan, args.output); return 0
        if args.cmd == "hydrate":
            write_json(hydrate(plan), args.output); return 0
        if args.cmd == "fetch":
            hydrated = json.loads(args.hydration.read_text()) if args.hydration else None
            cache = args.cache_dir if args.cache_dir.is_absolute() else root / args.cache_dir
            result = fetch(plan, cache, hydrated); write_json(result, args.output); return 2 if result["fetch_failures"] else 0
        if args.cmd == "build":
            lock = json.loads(args.lock.read_text()); out = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
            build(lock, out, args.target, root); return 0
        raise PackError(f"unhandled command: {args.cmd}")
    except PackError as exc:
        print(f"error: {exc}", file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
