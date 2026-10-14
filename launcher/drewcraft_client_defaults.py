#!/usr/bin/env python3
"""Seed and preserve DrewCraft's client-owned graphics defaults.

The release manifest owns gameplay/compatibility files. Graphics preferences are
user-owned: a clean install starts on the conservative Potato preset, then the
launcher carries the player's Simple Clouds and Distant Horizons choices across
versioned Prism instances without overwriting later edits.
"""
from __future__ import annotations

import json
import hashlib
import importlib.util
import os
import pathlib
import re
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


DH_FUNCTIONAL_DEFAULTS = {
    # Actual DH 3.3.1 config paths, verified against its packaged Config classes.
    ("[common.worldGenerator]", "generatorPlan"): '"CHUNKS_ONLY"',
    ("[common.worldGenerator]", "chunkGeneratorMode"): '"PRE_EXISTING_ONLY"',
    ("[client.advanced.graphics.culling]", "overdrawPrevention"): '"0.2"',
    ("[client.advanced.graphics.culling]", "reduceOverdrawWithFastMovement"): "true",
}


def ensure_dh_functional_defaults(minecraft_dir: pathlib.Path, *, migrate_flight_settings: bool = False) -> bool:
    """Merge missing functional DH keys without touching user values.

    A one-time flight migration updates just these four keys. Subsequent runs
    preserve player changes; render distance, quality and all other keys stay.
    """
    path = minecraft_dir / pathlib.Path("config/DistantHorizons.toml")
    try:
        text = path.read_text("utf-8") if path.is_file() else ""
    except OSError:
        return False
    lines = text.splitlines()
    changed = False
    # Remove the inert key shipped by launcher 0.1.11, only in its old table.
    table = ""
    retained = []
    for line in lines:
        if line.strip().startswith("["):
            table = line.strip()
        if table == "[client.advanced.worldGenerator]" and re.match(r"\s*enableDistantGeneration\s*=", line):
            changed = True
            continue
        retained.append(line)
    lines = retained
    for (table, key), value in DH_FUNCTIONAL_DEFAULTS.items():
        header = next((i for i, line in enumerate(lines)
                       if line.strip() == table), None)
        if header is None:
            if lines and lines[-1].strip():
                lines.append("")
            lines.append(table)
            lines.append(f"{key} = {value}")
        else:
            end = next((i for i in range(header + 1, len(lines))
                        if lines[i].strip().startswith("[")), len(lines))
            existing = next((i for i in range(header + 1, end)
                             if re.match(rf"\s*{re.escape(key)}\s*=", lines[i])), None)
            if existing is not None:
                if not migrate_flight_settings or lines[existing].strip() == f"{key} = {value}":
                    continue
                lines[existing] = f"{key} = {value}"
            else:
                lines.insert(header + 1, f"{key} = {value}")
        changed = True
    if changed or not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


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

    # Apply the owner-approved flight fix once, then preserve later user edits.
    flight_marker = app_dir / "user-data/dh-flight-defaults.json"
    migrate_flight = not flight_marker.is_file()
    ensure_dh_functional_defaults(minecraft_dir, migrate_flight_settings=migrate_flight)
    # Launcher updates alone must not upgrade the config of the older DH pack.
    dh_jar = minecraft_dir / 'mods/DistantHorizons-3.3.3-1.21.1-drewcraft.1.jar'
    if dh_jar.is_file():
        if hashlib.sha256(dh_jar.read_bytes()).hexdigest() != 'b43f5ac302a2ed6039d34f737d3182a0bc771333c71653c06aa7528cae6ecb67':
            raise RuntimeError('Unrecognized DH compatibility build; refusing config migration')
        try:
            from dh_config_upgrade import migrate
        except ModuleNotFoundError:
            spec = importlib.util.spec_from_file_location('drewcraft_dh_config_upgrade', pathlib.Path(__file__).with_name('dh_config_upgrade.py'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            migrate = module.migrate
        import tomllib
        path = minecraft_dir / 'config/DistantHorizons.toml'
        if tomllib.loads(path.read_text('utf-8')).get('_version') is not None:
            migrate(path)
    if migrate_flight:
        _atomic_json(flight_marker, {"schemaVersion": 1, "launcherVersion": "0.1.12"})

    # Cache the mod-owned client configs immediately so the very next pack
    # update can restore them even if no intermediate launcher run occurs.
    _cache_current_graphics(app_dir, minecraft_dir)
    return seeded
