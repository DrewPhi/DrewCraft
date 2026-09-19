#!/usr/bin/env python3
"""Seed and preserve DrewCraft's client-owned graphics defaults.

The release manifest owns gameplay/compatibility files. Graphics preferences are
user-owned: a clean install starts on the conservative Potato preset, then the
launcher carries the player's Simple Clouds and Distant Horizons choices across
versioned Prism instances without overwriting later edits.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import tempfile

PROFILE_SCHEMA_VERSION = 1
PROFILE_NAME = "potato"

ENTITY_CULLING_PATH = "config/entityculling.json"
IV_ENTITY_WHITELIST = (
    "mts:builder_existing",
    "mts:builder_rendering",
    "mts:builder_seat",
)

# options.txt is already preserved by drewcraft_bootstrap. These mod configs
# need the same treatment, but must stay outside the immutable release truth so
# users can turn graphics up without the repair path resetting them.
#
# NOTE: Distant Horizons keeps server and client settings in a single file at
# config/DistantHorizons.toml (singular "config"). There is no "configs/"
# directory on real NeoForge installs; writing there would silently do nothing.
PRESERVED_GRAPHICS_PATHS = (
    "config/simpleclouds-client.toml",
    "config/DistantHorizons.toml",
)

# Max-potato vanilla defaults, seeded only for missing keys on first launch.
# Key names/values verified against the 1.21.1 options surface:
# - graphicsMode 0 = Fast (1 = Fancy default, 2 = Fabulous);
# - particles 2 = Minimal; renderClouds false = off;
# - mipmapLevels 0, biomeBlendRadius 0, entityDistanceScaling 0.5 (minimums);
# - ao 0 = smooth lighting off under either int or boolean parsing.
# Unknown keys are ignored by vanilla, so this degrades safely on any version.
POTATO_OPTION_DEFAULTS = {
    "renderDistance": "6",
    "simulationDistance": "5",
    "graphicsMode": "0",
    "particles": "2",
    "maxFps": "60",
    "renderClouds": "false",
    "mipmapLevels": "0",
    "biomeBlendRadius": "0",
    "entityDistanceScaling": "0.5",
    "entityShadows": "false",
    "enableVsync": "false",
    "ao": "0",
}

POTATO_DEFAULT_FILES = {
    "config/simpleclouds-client.toml": (
        "# DrewCraft Potato defaults: client visuals only. Weather/gameplay state remains server-authoritative.\n"
        "[visual]\n"
        "transparency = false\n"
        "atmosphericClouds = false\n"
        "\n"
        "[performance]\n"
        "renderStormFog = false\n"
        'levelOfDetail = "LOW"\n'
        "\n"
        "[performance.mesh_generation]\n"
        'generationInterval = "DYNAMIC"\n'
        "framesToGenerateMesh = 20\n"
        "\n"
        "[distant_horizons]\n"
        "distantShadows = false\n"
        "shadowDistance = 1000\n"
    ),
    "config/DistantHorizons.toml": (
        "# DrewCraft Potato default: keep long-distance geography while limiting LOD radius.\n"
        "_version = 4\n"
        "\n"
        "[client.advanced.graphics.quality]\n"
        "lodChunkRenderDistanceRadius = 32\n"
    ),
}


def _user_data_root(app_dir: pathlib.Path) -> pathlib.Path:
    return app_dir / "user-data" / "graphics"


def _marker_path(app_dir: pathlib.Path) -> pathlib.Path:
    return app_dir / "user-data" / "client-defaults.json"


def _minecraft_dir_from_state(state: dict) -> pathlib.Path | None:
    prism_root = state.get("prismRoot")
    instance_id = state.get("instanceId")
    if not prism_root or not instance_id:
        return None
    return pathlib.Path(prism_root) / "instances" / str(instance_id) / "minecraft"


def _current_minecraft_dir(app_dir: pathlib.Path) -> pathlib.Path | None:
    state_path = app_dir / "state.json"
    if not state_path.is_file():
        return None
    try:
        state = json.loads(state_path.read_text("utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return _minecraft_dir_from_state(state)


def _atomic_json(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, sort_keys=True, separators=(",", ":"))
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def snapshot_user_graphics(app_dir: pathlib.Path) -> None:
    """Mirror mutable graphics configs from the current Prism instance.

    This runs before release convergence, while the previous versioned instance
    still exists. Missing source files remove stale cached copies so deliberately
    deleting/resetting a config cannot resurrect an older preference later.
    """
    minecraft_dir = _current_minecraft_dir(app_dir)
    if minecraft_dir is None or not minecraft_dir.is_dir():
        return

    cache_root = _user_data_root(app_dir)
    for rel in PRESERVED_GRAPHICS_PATHS:
        source = minecraft_dir / pathlib.Path(rel)
        cached = cache_root / pathlib.Path(rel)
        if source.is_file():
            cached.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, cached)
        elif cached.exists():
            cached.unlink()


def _merge_missing_options(options_path: pathlib.Path) -> None:
    """Add Potato option keys without replacing Minecraft/user-owned values."""
    try:
        text = options_path.read_text("utf-8") if options_path.is_file() else ""
    except OSError:
        text = ""
    lines = text.splitlines()
    present = {line.split(":", 1)[0] for line in lines if ":" in line}
    changed = False
    for key, value in POTATO_OPTION_DEFAULTS.items():
        if key not in present:
            lines.append(f"{key}:{value}")
            changed = True
    if changed or not options_path.exists():
        options_path.parent.mkdir(parents=True, exist_ok=True)
        options_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _restore_cached_graphics(app_dir: pathlib.Path, minecraft_dir: pathlib.Path) -> None:
    cache_root = _user_data_root(app_dir)
    for rel in PRESERVED_GRAPHICS_PATHS:
        cached = cache_root / pathlib.Path(rel)
        target = minecraft_dir / pathlib.Path(rel)
        if cached.is_file() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cached, target)


def _cache_current_graphics(app_dir: pathlib.Path, minecraft_dir: pathlib.Path) -> None:
    cache_root = _user_data_root(app_dir)
    for rel in PRESERVED_GRAPHICS_PATHS:
        source = minecraft_dir / pathlib.Path(rel)
        cached = cache_root / pathlib.Path(rel)
        if source.is_file():
            cached.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, cached)


def ensure_vehicle_entity_culling_whitelist(minecraft_dir: pathlib.Path) -> bool:
    """Keep Immersive Vehicles visible without removing user culling entries."""
    path = minecraft_dir / pathlib.Path(ENTITY_CULLING_PATH)
    try:
        payload = json.loads(path.read_text("utf-8")) if path.is_file() else {}
    except (OSError, ValueError, TypeError):
        # Never destroy a hand-edited or partially-written config. Entity
        # Culling will recreate it on the next client start.
        return False
    changed = False
    for key in ("entityWhitelist", "tickCullingWhitelist"):
        values = payload.get(key)
        if not isinstance(values, list):
            values = []
            payload[key] = values
            changed = True
        for identifier in IV_ENTITY_WHITELIST:
            if identifier not in values:
                values.append(identifier)
                changed = True
    if changed or not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return changed


def apply_client_defaults(app_dir: pathlib.Path, state: dict) -> bool:
    """Restore user graphics settings and seed Potato exactly once.

    Returns True only when the first-launch Potato marker is created. Existing
    files always win, so adopting this launcher on an existing DrewCraft install
    cannot downgrade settings the user already chose.
    """
    minecraft_dir = _minecraft_dir_from_state(state)
    if minecraft_dir is None:
        raise RuntimeError("DrewCraft launcher state is missing its Prism instance")
    minecraft_dir.mkdir(parents=True, exist_ok=True)

    _restore_cached_graphics(app_dir, minecraft_dir)
    ensure_vehicle_entity_culling_whitelist(minecraft_dir)

    marker = _marker_path(app_dir)
    seeded = False
    if not marker.is_file():
        # The managed-resource-pack step may already have created options.txt.
        # Merge only absent graphics keys so resourcePacks and user choices win.
        _merge_missing_options(minecraft_dir / "options.txt")

        for rel, content in POTATO_DEFAULT_FILES.items():
            target = minecraft_dir / pathlib.Path(rel)
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        _atomic_json(marker, {
            "schemaVersion": PROFILE_SCHEMA_VERSION,
            "graphicsPreset": PROFILE_NAME,
            "packVersion": state.get("packVersion"),
            "instanceId": state.get("instanceId"),
        })
        seeded = True

    # Cache the mod-owned client configs immediately so the very next pack
    # update can restore them even if no intermediate launcher run occurs.
    _cache_current_graphics(app_dir, minecraft_dir)
    return seeded
