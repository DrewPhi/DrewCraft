#!/usr/bin/env python3
"""Covenant lore/clue fragment logic (pure, testable, no Minecraft boot).

Implements pack/content/lore/config.json drop_and_coordinate_rules:
- coordinate modes with the frozen distribution (x_only .38 / z_only .38 /
  x_y .09 / z_y .09 / x_z .045 / full .015);
- DIVIDED WAYMARK page template with [withheld] for missing axes;
- 75% home-site / 25% random-uncleared field-book targeting;
- cleared-site residue weight (default 5%) so obsolete clues fade but remain.

Coordinates are supplied by the caller from the production-world site
registry; this module never invents world geography.
"""
from __future__ import annotations

import json
import pathlib
import random
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "pack" / "content" / "lore" / "config.json"

MODES = ("x_only", "z_only", "x_y", "z_y", "x_z", "x_y_z_full")

_MODE_AXES: dict[str, tuple[str, ...]] = {
    "x_only": ("x",),
    "z_only": ("z",),
    "x_y": ("x", "y"),
    "z_y": ("z", "y"),
    "x_z": ("x", "z"),
    "x_y_z_full": ("x", "y", "z"),
}


def load_config(path: pathlib.Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def distribution(config: dict[str, Any] | None = None) -> dict[str, float]:
    cfg = config or load_config()
    dist = cfg["drop_and_coordinate_rules"]["coordinate_fragment_distribution"]
    total = sum(float(dist[m]) for m in MODES)
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"coordinate distribution must sum to 1.0, got {total}")
    return {m: float(dist[m]) for m in MODES}


def roll_mode(rng: random.Random, config: dict[str, Any] | None = None) -> str:
    dist = distribution(config)
    roll = rng.random()
    cumulative = 0.0
    for mode in MODES:
        cumulative += dist[mode]
        if roll < cumulative:
            return mode
    return MODES[-1]


def render_waymark(target_display: str, coords: dict[str, int], mode: str,
                   config: dict[str, Any] | None = None) -> list[str]:
    """Render the DIVIDED WAYMARK page lines for a site + coordinate mode."""
    if mode not in _MODE_AXES:
        raise ValueError(f"unknown coordinate mode: {mode}")
    cfg = config or load_config()
    template: list[str] = cfg["drop_and_coordinate_rules"]["waymark_page_template"]
    shown = set(_MODE_AXES[mode])

    def fmt(axis: str) -> str:
        upper = axis.upper()
        if axis in shown:
            if axis not in coords:
                raise ValueError(f"mode {mode} needs coordinate {axis}")
            return str(coords[axis])
        return "[withheld]"

    lines = []
    for line in template:
        lines.append(
            line.replace("{TARGET_DISPLAY}", target_display)
            .replace("{X_OR_WITHHELD}", fmt("x"))
            .replace("{Y_OR_WITHHELD}", fmt("y"))
            .replace("{Z_OR_WITHHELD}", fmt("z"))
        )
    # Guarantee the destination seal is matchable: target name must appear.
    if not any(target_display in line for line in lines):
        raise ValueError("waymark template dropped the target display name")
    return lines


def choose_field_book_site(rng: random.Random, home_site_id: str | None,
                           uncleared_site_ids: list[str]) -> str:
    """75% home site (if set), else 25% random uncleared. Falls back to home
    when no uncleared sites are known (all cleared -> residue handling)."""
    if home_site_id and rng.random() < 0.75:
        return home_site_id
    if uncleared_site_ids:
        return rng.choice(uncleared_site_ids)
    if home_site_id:
        return home_site_id
    raise ValueError("no site to target: home is None and uncleared list is empty")


def site_weight(site_id: str, cleared_site_ids: set[str], residue: float = 0.05) -> float:
    """Cleared sites drop to a small historical residue so players are not
    flooded with obsolete coordinates but can still find keepsakes."""
    return residue if site_id in cleared_site_ids else 1.0
