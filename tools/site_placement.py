#!/usr/bin/env python3
"""Site-placement scoring for cult structures on real Terrain Diffusion terrain.

Scores candidate locations per archetype without requiring Minecraft: given a
heightmap sample grid and context, produce a deterministic 0-100 score plus
the disqualifying reason (if any). Visual beauty stays human; geometry fit,
slope discipline, and spacing rules are automatable.
"""
from __future__ import annotations

import math


def slope_stats(heights: list[list[float]]) -> tuple[float, float]:
    """Mean and max neighbor height delta over the grid."""
    deltas = []
    rows, cols = len(heights), len(heights[0])
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                deltas.append(abs(heights[r][c + 1] - heights[r][c]))
            if r + 1 < rows:
                deltas.append(abs(heights[r + 1][c] - heights[r][c]))
    if not deltas:
        return 0.0, 0.0
    return sum(deltas) / len(deltas), max(deltas)


def score_site(*, archetype: str, heights: list[list[float]],
               near_water: bool, distance_from_spawn: float,
               nearest_site_distance: float, cell_blocks: float = 64.0) -> dict:
    """Score 0-100. Archetype preferences encode end_game_plans.md §9."""
    mean_slope, max_slope = slope_stats(heights)
    footprint = len(heights) * len(heights[0]) * cell_blocks * cell_blocks
    reasons = []
    score = 100.0

    steep_ok = archetype in ("mountain temple", "plateau citadel")
    if max_slope > (24.0 if steep_ok else 8.0):
        reasons.append(f"max slope {max_slope:.1f} exceeds {archetype} limit")
        score -= 60.0
    score -= min(30.0, mean_slope * 3.0)

    if archetype in ("river/bridge stronghold",) and not near_water:
        reasons.append("river archetype requires water")
        score -= 50.0
    if near_water and archetype in ("mountain temple",):
        score -= 5.0

    if distance_from_spawn < 1024:
        reasons.append("too close to spawn")
        score -= 40.0
    if nearest_site_distance < 2048:
        reasons.append("too close to another cult site")
        score -= 40.0

    if footprint < 48 * 48:
        reasons.append("footprint too small for modules")
        score -= 25.0

    return {
        "score": max(0.0, round(score, 1)),
        "accepted": not reasons and score >= 60.0,
        "reasons": reasons,
        "mean_slope": round(mean_slope, 2),
        "max_slope": round(max_slope, 2),
        "footprint_blocks": footprint,
    }


def rank(candidates: list[dict]) -> list[dict]:
    """Deterministic rank: score desc, then distance from spawn desc."""
    return sorted(candidates,
                  key=lambda c: (-c["result"]["score"], -c.get("distance_from_spawn", 0.0)))
