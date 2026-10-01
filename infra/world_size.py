#!/usr/bin/env python3
"""Read-only live world usage and explicitly separated generation checkpoints."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
from region_inventory import linear_slots


def measure(world: Path, state_file: Path) -> dict:
    if not world.is_dir():
        raise ValueError(f"World directory does not exist: {world}")
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    total = allocated = dh = 0
    chunks = 0
    bounds = None
    region_files = placeholders = 0
    coordinates = set()
    for path in world.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            stat = path.stat()
            total += stat.st_size
            allocated += getattr(stat, "st_blocks", math.ceil(stat.st_size / 512)) * 512
            if "distanthorizons" in path.name.lower():
                dh += stat.st_size
            if path.parent != world / "region" or path.suffix not in (".mca", ".linear"):
                continue
            parts = path.name.split(".")
            if len(parts) != 4 or parts[0] != "r":
                continue
            rx, rz = int(parts[1]), int(parts[2])
            if (rx, rz) in coordinates:
                raise ValueError(f'Duplicate Anvil/Linear region at {rx},{rz}; finish conversion before inventory')
            coordinates.add((rx, rz))
            if path.suffix == '.linear':
                slots = linear_slots(path)
            else:
                if stat.st_size < 8192:
                    placeholders += 1
                    continue
                with path.open("rb") as stream:
                    header = stream.read(4096)
                if len(header) != 4096:
                    placeholders += 1
                    continue
                slots = [slot for slot in range(1024)
                         if int.from_bytes(header[slot*4:slot*4+3], 'big') >= 2
                         and header[slot*4+3]]
            region_files += 1
            for slot in slots:
                x, z = (rx * 32 + slot % 32) * 16, (rz * 32 + slot // 32) * 16
                chunks += 1
                if bounds is None:
                    bounds = [x, x + 15, z, z + 15]
                else:
                    bounds = [min(bounds[0], x), max(bounds[1], x + 15),
                              min(bounds[2], z), max(bounds[3], z + 15)]
        except FileNotFoundError:
            continue  # Live generation can replace files during this snapshot.
    radius = state.get("continuousCompletedRadius") if state.get("continuousChunky") else None
    return {
        "schemaVersion": 1,
        "measuredUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "worldPath": str(world), "worldSizeBytes": total,
        "allocatedDiskBytes": allocated, "dhSizeBytes": dh,
        "targetBytes": state.get("targetBytes"),
        "chunkyCompletedRadiusBlocks": radius,
        "chunkyCompletedDiameterBlocks": radius * 2 if radius is not None else None,
        "chunkyInProgressTargetRadiusBlocks": state.get("continuousTargetRadius")
            if state.get("phase") == "continuous_chunky" else None,
        "playableRadiusBlocks": max(0, radius - state.get("boundaryBufferBlocks", 320))
            if radius is not None and state.get("enforcePregenBoundary") else None,
        "storedOverworldChunkEntries": chunks,
        "savedOverworldBoundsBlocks": bounds,
        "nonemptyOverworldRegionFiles": region_files,
        "emptyOrShortRegionPlaceholders": placeholders,
        "phase": state.get("phase"),
        "checkpointUpdatedUtc": state.get("updatedUtc"),
        "notes": ["Live, non-atomic snapshot; all dimensions and DH are included in world size.",
                  "Stored entries can include partial chunks; bounds are not a filled rectangle.",
                  "Completed circle comes from fresh Chunky task completion, not legacy radius counters.",
                  "Checkpoint completion is not an independent per-chunk or LOD audit."],
    }


def render(report: dict) -> str:
    def size(value):
        return f"{value / 1e9:.2f} GB ({value / 1024**3:.2f} GiB)"
    lines = [f"World size (all dimensions + DH): {size(report['worldSizeBytes'])}",
             f"Allocated disk space: {size(report['allocatedDiskBytes'])}",
             f"DH files (included above): {size(report['dhSizeBytes'])}"]
    if report["targetBytes"] is not None:
        lines.append(f"World storage target: {size(report['targetBytes'])}")
    radius = report["chunkyCompletedRadiusBlocks"]
    lines.append("Chunky-confirmed circle: unknown (legacy counters ignored)" if radius is None
                 else f"Chunky-confirmed circle: radius {radius:,} blocks; diameter {radius * 2:,} blocks")
    target = report["chunkyInProgressTargetRadiusBlocks"]
    if target is not None:
        lines.append(f"Chunky IN-PROGRESS target: radius {target:,} blocks (NOT completed)")
    if report["playableRadiusBlocks"] is not None:
        lines.append(f"Playable border radius: {report['playableRadiusBlocks']:,} blocks")
    bounds = report["savedOverworldBoundsBlocks"]
    if bounds:
        x0, x1, z0, z1 = bounds
        lines.append(f"Saved chunk footprint: X {x0:,}..{x1:,}; Z {z0:,}..{z1:,} "
                     f"({x1-x0+1:,} × {z1-z0+1:,} blocks; irregular, may include partial chunks)")
    lines.extend([f"Stored Overworld chunk entries: {report['storedOverworldChunkEntries']:,}",
                  f"Snapshot: {report['measuredUtc']} (live; size can change while reading)"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", type=Path, default=Path("/srv/drewcraft/persistent/world"))
    parser.add_argument("--state", type=Path, default=Path("/srv/drewcraft/state/pregen.json"))
    parser.add_argument("--json", action="store_true", help="Machine-readable measurements, in bytes and blocks")
    args = parser.parse_args()
    try:
        report = measure(args.world, args.state)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"World size check failed: {exc}\n")
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
