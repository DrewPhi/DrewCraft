#!/usr/bin/env python3
"""Validate and lock an approved DrewCraft production-world candidate.

The expensive Terrain Diffusion/Chunky generation happens on suitable hardware.
This tool consumes the resulting measured report and refuses to freeze seed/radius
until objective restore/archive measurements and explicit visual/geographic review
have all passed.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import re

SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_POSITIVE_METRICS = (
    "generationSeconds",
    "worldBytes",
    "archiveBytes",
    "backupSeconds",
    "restoreSeconds",
    "restartSeconds",
)
REQUIRED_REVIEWS = (
    "visualTerrainQuality",
    "sourceDistribution",
    "herdCorridorQuality",
)


def validate_candidate(plan: dict, report: dict) -> dict:
    if plan.get("schemaVersion") != 1 or report.get("schemaVersion") != 1:
        raise RuntimeError("unsupported production-world plan/report schema")
    if report.get("worldId") != plan.get("worldId"):
        raise RuntimeError("candidate worldId does not match production plan")
    if report.get("worldRevision") != plan.get("worldRevision"):
        raise RuntimeError("candidate worldRevision does not match production plan")
    if report.get("generationPackVersion") != plan.get("generationPackVersion"):
        raise RuntimeError("candidate generationPackVersion does not match production plan")

    terrain = plan.get("terrain", {})
    radius = report.get("pregenRadiusBlocks")
    if radius not in terrain.get("candidateRadiiBlocks", []):
        raise RuntimeError(f"candidate radius {radius!r} is not an approved experiment radius")
    seed = report.get("seed")
    if not isinstance(seed, int):
        raise RuntimeError("candidate seed must be an integer")

    metrics = report.get("metrics", {})
    for name in REQUIRED_POSITIVE_METRICS:
        value = metrics.get(name)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise RuntimeError(f"candidate metric {name} must be positive")
    if metrics.get("cleanRestoreVerified") is not True:
        raise RuntimeError("candidate must pass clean off-host restore verification")

    archive_sha = report.get("worldArchiveSha256", "")
    if not isinstance(archive_sha, str) or not SHA256.fullmatch(archive_sha.lower()):
        raise RuntimeError("candidate requires a valid world archive SHA-256")

    reviews = report.get("reviews", {})
    for name in REQUIRED_REVIEWS:
        review = reviews.get(name)
        if not isinstance(review, dict) or review.get("pass") is not True:
            raise RuntimeError(f"candidate review {name} has not passed")
        if not str(review.get("notes", "")).strip():
            raise RuntimeError(f"candidate review {name} requires notes")

    return report


def lock_candidate(plan: dict, report: dict) -> dict:
    validate_candidate(plan, report)
    if plan.get("status") not in ("candidate_selection_required", "locked"):
        raise RuntimeError(f"production plan cannot be locked from status {plan.get('status')!r}")
    locked = copy.deepcopy(plan)
    locked["status"] = "locked"
    locked["terrain"]["seed"] = report["seed"]
    locked["terrain"]["pregenRadiusBlocks"] = report["pregenRadiusBlocks"]
    locked["terrain"]["lockedCandidate"] = {
        "candidateId": report.get("candidateId"),
        "generationPackVersion": report["generationPackVersion"],
        "worldArchiveSha256": report["worldArchiveSha256"].lower(),
        "metrics": report["metrics"],
        "reviews": report["reviews"],
    }
    return locked


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="world/production-world.plan.json")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    plan = json.loads(pathlib.Path(args.plan).read_text("utf-8"))
    report = json.loads(pathlib.Path(args.candidate).read_text("utf-8"))
    locked = lock_candidate(plan, report)
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(locked, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "locked",
        "candidateId": report.get("candidateId"),
        "generationPackVersion": report["generationPackVersion"],
        "seed": report["seed"],
        "pregenRadiusBlocks": report["pregenRadiusBlocks"],
        "worldArchiveSha256": report["worldArchiveSha256"].lower(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
