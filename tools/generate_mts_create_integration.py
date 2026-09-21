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
NEW_WIRE = "createaddition:copper_wire"
NEW_FASTENER = "minecraft:iron_nugget"
NUGGET_IRON = 1.0 / 9.0


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
    #   * screws -> vanilla iron nuggets (the exact old 1/9-ingot fastener cost)
    #
    # Old plating/tubes cost 49/90 ingot each rather than exactly 1/2. The
    # difference is 0.4 iron nugget per unit, so a small rounded nugget
    # compensation makes large and small recipes converge to the legacy cost.
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


def find_mts_material_lists(zf: zipfile.ZipFile) -> Iterable[tuple[str, str, list[list[str]]]]:
    prefix = "assets/mtsofficialpack/jsondefs/"
    for name in sorted(zf.namelist()):
        if not name.startswith(prefix) or not name.endswith(".json"):
            continue
        parts = name.split("/")
        if len(parts) < 5:
            continue
        classification = parts[3]
        if classification not in {"vehicles", "parts", "items", "decors", "poles", "bullets", "instruments"}:
            continue
        text = zf.read(name).decode("utf-8", errors="replace")
        lists = extract_array(text, "materialLists")
        if not lists:
            continue
        if not isinstance(lists, list) or not all(isinstance(x, list) for x in lists):
            continue
        yield classification, Path(name).stem, lists


def build_mts_overrides(official_pack: Path) -> tuple[dict, dict]:
    overrides: dict[str, dict] = {"mtsofficialpack": {}}
    rows: list[dict] = []
    balance_violations: list[dict] = []
    with zipfile.ZipFile(official_pack) as zf:
        for classification, system_name, lists in find_mts_material_lists(zf):
            transformed_lists: list[list[str]] = []
            audits: list[dict] = []
            for mats in lists:
                transformed, audit = transform_material_list(mats)
                transformed_lists.append(transformed)
                audits.append(audit)
            overrides["mtsofficialpack"][system_name] = {"commonMaterialLists": transformed_lists}
            max_delta = max((abs(a["generic_iron_delta_percent"]) for a in audits if a["generic_iron_delta_percent"] is not None), default=0.0)
            row = {
                "classification": classification,
                "system_name": system_name,
                "variants": audits,
                "max_abs_generic_iron_delta_percent": round(max_delta, 2),
            }
            rows.append(row)
            if max_delta > 10.0:
                balance_violations.append(row)

    if balance_violations:
        names = ", ".join(f"{r['classification']}/{r['system_name']}" for r in balance_violations)
        raise SystemExit(f"MTS recipe balance gate failed (>10% generic iron delta): {names}")

    report = {
        "schema_version": 1,
        "source": str(official_pack.name),
        "policy": "Create owns generic stock; MTS owns functional vehicle components and final assembly.",
        "legacy_costs": {
            "plating_iron_equivalent": PLATING_IRON,
            "screw_iron_equivalent": SCREW_IRON,
            "tube_iron_equivalent": TUBE_IRON,
        },
        "recipe_balance_gate_percent": 10.0,
        "vehicle_balance_gate_percent": 10.0,
        "overridden_item_count": len(rows),
        "rows": rows,
    }
    wrapper = {
        "comment1": "DrewCraft 0.1.8 integration: generated from the exact pinned MTS Official Pack V29.",
        "comment2": "Generic MTS sheet/screw/tube/wire inputs are replaced by Create/Crafts & Additions stock while MTS functional parts remain MTS.",
        "comment3": "Do not hand edit this generated file; regenerate it with tools/generate_mts_create_integration.py.",
        "overrides": overrides,
    }
    return wrapper, report


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def shaped(pattern: list[str], key: dict, result: str, count: int = 1) -> dict:
    return {
        "type": "minecraft:crafting_shaped",
        "category": "misc",
        "pattern": pattern,
        "key": key,
        "result": {"id": result, "count": count},
    }


def shapeless(ingredients: list[dict], result: str, count: int = 1) -> dict:
    return {
        "type": "minecraft:crafting_shapeless",
        "category": "misc",
        "ingredients": ingredients,
        "result": {"id": result, "count": count},
    }


def item(name: str) -> dict:
    return {"item": name}


def tag(name: str) -> dict:
    return {"tag": name}


def write_component_recipes(datapack: Path) -> None:
    base = datapack / "data/mtsofficialpack/recipe"
    recipes = {
        "piston": shapeless(
            [item("create:iron_sheet"), item("createaddition:iron_rod")],
            "mts:mtsofficialpack.piston", 2,
        ),
        "spring": shapeless(
            [item("createaddition:iron_wire"), tag("c:nuggets/iron"), tag("c:nuggets/iron")],
            "mts:mtsofficialpack.spring", 1,
        ),
        "sparkplug": shapeless(
            [item("createaddition:iron_rod"), item("createaddition:iron_rod"), item("createaddition:copper_wire"), tag("c:gems/quartz")],
            "mts:mtsofficialpack.sparkplug", 2,
        ),
        "headlight": shapeless(
            [item("create:iron_sheet"), item("create:iron_sheet"), item("createaddition:copper_wire"), item("minecraft:redstone_lamp"), tag("c:glass_panes/colorless")],
            "mts:mtsofficialpack.headlight", 2,
        ),
        "circuit": shapeless(
            [item("create:electron_tube"), item("createaddition:copper_wire"), item("mts:mtsofficialpack.plastic")],
            "mts:mtsofficialpack.circuit", 2,
        ),
        "processor": shapeless(
            [item("create:precision_mechanism"), item("mts:mtsofficialpack.circuit"), item("mts:mtsofficialpack.circuit"), item("createaddition:iron_rod")],
            "mts:mtsofficialpack.processor", 2,
        ),
        "blowtorch": shapeless(
            [item("createaddition:iron_rod"), item("mts:mtsofficialpack.solidfuel")],
            "mts:mtsofficialpack.blowtorch", 1,
        ),
        "repairkit": shapeless(
            [item("mts:mtsofficialpack.blowtorch"), item("mts:mts.wrench"), item("minecraft:diamond"), item("createaddition:iron_rod"), item("createaddition:copper_wire"), item("minecraft:chest")],
            "mts:mtsofficialpack.repairkit", 1,
        ),
        "hydraulics": shapeless(
            [item("create:fluid_pipe"), item("create:copper_sheet"), item("create:copper_sheet"), item("createaddition:iron_rod"), item("createaddition:iron_rod"), item("create:andesite_alloy")],
            "mts:mtsofficialpack.hydraulics", 1,
        ),
        "armorplate": shapeless(
            [item("create:sturdy_sheet"), item("create:iron_sheet"), item("create:iron_sheet")],
            "mts:mtsofficialpack.armorplate", 2,
        ),
    }
    for name, data in recipes.items():
        write_json(base / f"{name}.json", data)


def industrial_loot_pool() -> dict:
    def loot_item(name: str, weight: int, min_count: int = 1, max_count: int = 1) -> dict:
        entry = {"type": "minecraft:item", "name": name, "weight": weight}
        if max_count > 1 or min_count != 1:
            entry["functions"] = [{
                "function": "minecraft:set_count",
                "count": {"type": "minecraft:uniform", "min": min_count, "max": max_count},
            }]
        return entry
    return {
        "name": "drewcraft:industrial_salvage",
        "rolls": 1,
        "conditions": [{"condition": "minecraft:random_chance", "chance": 0.12}],
        "entries": [
            loot_item("create:iron_sheet", 10, 2, 6),
            loot_item("create:copper_sheet", 7, 1, 4),
            loot_item("create:brass_sheet", 5, 1, 3),
            loot_item("create:electron_tube", 5, 1, 3),
            loot_item("create:precision_mechanism", 2, 1, 1),
            loot_item("mts:mtsofficialpack.circuit", 3, 1, 2),
            loot_item("mts:mtsofficialpack.processor", 1, 1, 1),
        ],
    }


def write_wda_overrides(wda_jar: Path, datapack: Path) -> dict:
    changed: list[str] = []
    with zipfile.ZipFile(wda_jar) as zf:
        for name in sorted(zf.namelist()):
            normalized = name.replace("\\", "/")
            if not normalized.endswith(".json") or not normalized.startswith("data/dungeons_arise/"):
                continue
            if "/loot_table/chests/" not in normalized and "/loot_tables/chests/" not in normalized:
                continue
            try:
                table = json.loads(zf.read(name).decode("utf-8"))
            except Exception:
                continue
            if not isinstance(table, dict) or not isinstance(table.get("pools"), list):
                continue
            if any(isinstance(p, dict) and p.get("name") == "drewcraft:industrial_salvage" for p in table["pools"]):
                continue
            table["pools"].append(industrial_loot_pool())
            write_json(datapack / normalized, table)
            changed.append(normalized)
    return {"modified_wda_loot_tables": len(changed), "paths": changed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--official-pack", type=Path, required=True)
    ap.add_argument("--wda-jar", type=Path, required=True)
    ap.add_argument("--overlay", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    args.overlay.mkdir(parents=True, exist_ok=True)
    mts_override, balance = build_mts_overrides(args.official_pack)
    write_json(args.overlay / "config/mtscraftingoverrides.json", mts_override)

    datapack = args.overlay / "datapacks/drewcraft-integration"
    write_json(datapack / "pack.mcmeta", {
        "pack": {
            "pack_format": 48,
            "description": "DrewCraft 0.1.8 Create/MTS/WDA integration",
        }
    })
    write_component_recipes(datapack)
    loot = write_wda_overrides(args.wda_jar, datapack)

    balance["wda_loot_integration"] = loot
    balance["component_recipe_overrides"] = [
        "piston", "spring", "sparkplug", "headlight", "circuit", "processor",
        "blowtorch", "repairkit", "hydraulics", "armorplate",
    ]
    write_json(args.report, balance)
    print(f"mts_overrides={balance['overridden_item_count']} wda_loot_tables={loot['modified_wda_loot_tables']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
