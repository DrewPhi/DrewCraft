#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import zipfile
from pathlib import Path
from typing import Iterable

PLATING_IRON = 49.0 / 90.0
SCREW_IRON = 1.0 / 9.0
TUBE_IRON = PLATING_IRON
ROD_IRON = 0.5
SHEET_IRON = 1.0

OLD_PLATING = "mts:mtsofficialpack.plating"
OLD_SCREWS = "mts:mtsofficialpack.screws"
OLD_TUBE = "mts:mtsofficialpack.metaltube"
OLD_WIRE = "mts:mtsofficialpack.copperwire"

NEW_SHEET = "create:iron_sheet"
NEW_ROD = "createaddition:iron_rod"
NEW_WIRE = "createaddition:copper_wire"\nNEW_FASTENER = "minecraft:iron_nugget"\nNUGGET_IRON = 1.0 / 9.0


def round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def parse_material(value: str) -> tuple[str, int]:
    head, qty = value.rsplit(":", 1)
    return head, int(qty)


def fmt_material(item: str, qty: int) -> str:
    return f"{item}:{qty}"


def strip_json_comments(text: str) -> str:
    out: list[str] = []
    i = 0
    in_string = False
    escaped = False
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if in_string:
            out.append(c)
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if c == "/" and n == "/":
            i += 2
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        if c == "/" and n == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def extract_array(text: str, key: str) -> list | None:
    clean = strip_json_comments(text)
    marker = f'"{key}"'
    start_key = clean.find(marker)
    if start_key < 0:
        return None
    start = clean.find("[", start_key + len(marker))
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(clean)):
        c = clean[i]
        if in_string:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_string = False
            continue
        if c == '"':
            in_string = True
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return json.loads(clean[start : i + 1])
    return None


def transform_material_list(materials: list[str]) -> tuple[list[str], dict]:
    preserved: list[tuple[str, int]] = []
    plating = screws = tubes = old_wire = 0
    for raw in materials:
        item, qty = parse_material(raw)
        if item == OLD_PLATING:
            plating += qty
        elif item == OLD_SCREWS:
            screws += qty
        elif item == OLD_TUBE:
            tubes += qty
        elif item == OLD_WIRE:
            old_wire += qty
        else:
            preserved.append((item, qty))

    old_iron = plating * PLATING_IRON + screws * SCREW_IRON + tubes * TUBE_IRON

    # Preserve the industrial meaning of each legacy stock form while matching
    # its raw-iron burden closely:
    #   * pairs of plating -> Create sheets
    #   * an odd leftover plate -> one half-ingot C&A rod
    #   * tubes -> C&A rods
    #   * screws -> vanilla iron nuggets (exactly the old 1/9-ingot fastener cost)
    #
    # Old plating/tubes cost 49/90 ingot each rather than exactly 1/2. The
    # difference is 0.4 iron nugget per unit, so a small rounded nugget
    # compensation makes large and small recipes converge to the legacy cost
    # without retaining duplicate MTS stock items.
    sheets = plating // 2
    rods = (plating % 2) + tubes
    compensation_nuggets = round_half_up(0.4 * (plating + tubes))
    nuggets = screws + compensation_nuggets

    merged: dict[str, int] = {}
    order: list[str] = []
    for item, qty in preserved:
        if item not in merged:
            order.append(item)
            merged[item] = 0
        merged[item] += qty

    for item, qty in (
        (NEW_SHEET, sheets),
        (NEW_ROD, rods),
        (NEW_FASTENER, nuggets),
        (NEW_WIRE, old_wire),
    ):
        if qty <= 0:
            continue
        if item not in merged:
            order.append(item)
            merged[item] = 0
        merged[item] += qty

    result = [fmt_material(item, merged[item]) for item in order if merged[item] > 0]
    new_iron = sheets * SHEET_IRON + rods * ROD_IRON + nuggets * NUGGET_IRON
    delta = None if old_iron == 0 else (new_iron - old_iron) / old_iron * 100.0
    audit = {
        "legacy_plating": plating,
        "legacy_screws": screws,
        "legacy_tubes": tubes,
        "legacy_copper_wire": old_wire,
        "create_iron_sheets": sheets,
        "createaddition_iron_rods": rods,
        "minecraft_iron_nuggets": nuggets,
        "plating_tube_compensation_nuggets": compensation_nuggets,
        "createaddition_copper_wire": old_wire,
        "old_generic_iron_equivalent": round(old_iron, 4),
        "new_generic_iron_equivalent": round(new_iron, 4),
        "generic_iron_delta_percent": None if delta is None else round(delta, 2),
    }
    return result, audit

