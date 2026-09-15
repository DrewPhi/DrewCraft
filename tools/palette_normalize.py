#!/usr/bin/env python3
"""Offline block-palette normalization for the canonical cult structure kit.

Replaces block IDs according to a versioned palette map while preserving
compatible block-state properties and orientation (facing/half/shape/axis).
Unknown or mod-specific blocks are reported, never silently dropped.

Operates on schematic/palette data structures, never requires Minecraft.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

# State keys that are safe to carry across a palette swap when both blocks
# support them (orientation-sensitive: stairs/slabs/walls/fences/doors).
CARRIED_STATES = ("facing", "half", "shape", "axis", "type", "open", "hinge", "waterlogged")


def load_palette_map(path: pathlib.Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    mapping = data.get("mapping") or {}
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError(f"palette map {path} has no mapping")
    return {str(k): str(v) for k, v in mapping.items()}


def normalize_block(block_id: str, properties: dict[str, Any], palette: dict[str, str]) -> tuple[str, dict[str, Any]]:
    """Map one block ID through the palette, keeping compatible states."""
    target = palette.get(block_id, block_id)
    kept = {k: v for k, v in properties.items() if k in CARRIED_STATES}
    return target, kept


def normalize_palette(palette_blocks: list[dict[str, Any]], palette: dict[str, str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Normalize a schematic palette list. Returns (normalized, unmapped_ids)."""
    out: list[dict[str, Any]] = []
    unmapped: list[str] = []
    for entry in palette_blocks:
        block_id = str(entry.get("id"))
        props = dict(entry.get("properties") or {})
        new_id, new_props = normalize_block(block_id, props, palette)
        if block_id not in palette:
            unmapped.append(block_id)
        out.append({"id": new_id, "properties": new_props})
    return out, sorted(set(unmapped))
