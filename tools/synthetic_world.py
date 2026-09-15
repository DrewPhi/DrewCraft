#!/usr/bin/env python3
"""Synthetic integration world plan: a tiny disposable world exercising the
entire Covenant progression loop in CI without the final Terrain Diffusion
world or any human player.

Contents: one Source Core, one strategic source, one herd, Covenant mob
wave, Flightstone monument, and one fake aircraft target for flak.
All coordinates are local to the synthetic world (radius 256).
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]


def build_plan(seed: int = 1234) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "seed": seed,
        "radius_blocks": 256,
        "world_id": "drewcraft-synthetic",
        "flightstone": {"id": "flightstone", "pos": [0, 65, 0]},
        "source_core": {"id": "synthetic_core_01", "site_id": "ashen_gate", "pos": [48, 64, 0]},
        "strategic_source": {"id": "synthetic_source_01", "site_id": "ashen_gate",
                             "pos": [48, 64, 0], "faction": "drewcraft:covenant"},
        "herd": {"id": "synthetic_herd_01", "species": "cow", "count": 12, "pos": [-64, 64, 32]},
        "covenant_wave": {"template": "drewcraft:covenant_patrol", "strength": 12, "pos": [64, 65, 0]},
        "aircraft_target": {"id": "synthetic_aircraft_01", "pos": [48, 120, 96],
                            "velocity": [20, 0, 0]},
        "flak_zone": {"zone_id": "synthetic_flak_01", "site_id": "ashen_gate",
                      "center": [48, 70, 0], "radius_blocks": 128.0},
        "assertions": [
            "source registers exactly once across restart",
            "wave materializes under the active-entity cap",
            "casualties debit strategic strength idempotently",
            "Source Core clear persists and stops future launches",
            "clear archives the site clue and advances the Flightstone marker",
            "flak bursts appear near the predicted aircraft track with no block damage",
        ],
    }


def write_plan(path: pathlib.Path, seed: int = 1234) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_plan(seed), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="build/synthetic-world.json")
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args()
    out = write_plan(ROOT / args.output, args.seed)
    print(out)
