#!/usr/bin/env python3
"""Drive idle-only Chunky and Distant Horizons pregeneration safely.

Chunky owns terrain expansion.  Distant Horizons is run afterwards, over the
same already-generated radius, so the two generators never compete for the
same chunks.  Both jobs are paused when a player joins and resume from their
last checkpoint when the server is empty again.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import pwd
import re
import shutil
import tempfile
import time

from worldgen_guard import read_nbt, verify as verify_worldgen


def estimate_radius(current_radius: int, baseline_bytes: int, measured_bytes: int,
                    target_bytes: int) -> int:
    growth = measured_bytes - baseline_bytes
    target_growth = target_bytes - baseline_bytes
    if growth <= 0 or target_growth <= 0:
        raise ValueError("world growth and target growth must be positive")
    raw = current_radius * math.sqrt(target_growth / growth)
    return max(current_radius + 256, int(round(raw / 256.0)) * 256)


def tree_bytes(root: pathlib.Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def atomic_json(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, sort_keys=True, indent=2)
            fh.write("\n")
        os.replace(temp, path)
        os.chmod(path, 0o644)
        if os.geteuid() == 0:
            account = pwd.getpwnam("drewcraft")
            os.chown(path, account.pw_uid, account.pw_gid)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def online_players(response: str) -> int | None:
    """Parse vanilla's RCON ``list`` response without assuming its locale."""
    match = re.search(r"(?:There are\s+|players online:?\s*)(\d+)", response, re.IGNORECASE)
    return int(match.group(1)) if match else None


def task_running(response: str) -> bool:
    text = response.lower()
    return "task running" in text or "generating" in text or "generation running" in text


def dh_task_running(response: str) -> bool:
    text = response.lower()
    return task_running(response) and "not running" not in text and "no pre-generation" not in text


class Controller:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.world = pathlib.Path(args.world)
        self.state_path = pathlib.Path(args.state_file)
        self.health_path = pathlib.Path(args.health_file)
        self.password_path = pathlib.Path(args.password_file)
        self.boundary_path = self.world / "drewcraft-overworld-boundary.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_path.is_file():
            state = json.loads(self.state_path.read_text("utf-8"))
            # Migrate the original whole-radius controller state. An in-flight
            # task keeps its existing radius; future expansions use batches.
            state.setdefault("chunkyRadius", state.get("activeRadius", self.args.benchmark_radius))
            state.setdefault("dhRadius", 0)
            state.setdefault("dhTargetRadius", 0)
            state.setdefault("phaseAfterDh", "complete")
            return state
        state = {
            "schemaVersion": 2,
            "phase": "benchmark",
            "centerX": self.args.center_x,
            "centerZ": self.args.center_z,
            # A replacement world has a different baseline from the previous
            # generation. Measure the new world instead of trusting a stale
            # value baked into the systemd unit.
            "baselineBytes": tree_bytes(self.world),
            "benchmarkRadius": self.args.benchmark_radius,
            "activeRadius": self.args.benchmark_radius,
            "targetBytes": self.args.target_bytes,
            "maximumBytes": self.args.maximum_bytes,
            "minimumFreeBytes": self.args.minimum_free_bytes,
            "expansions": 0,
            "dhMaintenanceIntervalSeconds": self.args.dh_maintenance_interval_seconds,
            "dhMaintenanceActive": False,
            "maintenancePaused": False,
            "chunkyRadius": self.args.benchmark_radius,
            "dhRadius": 0,
            "dhTargetRadius": 0,
            "phaseAfterDh": "complete",
        }
        atomic_json(self.state_path, state)
        return state

    def save(self, **updates) -> None:
        self.state.update(updates)
        self.state["worldBytes"] = tree_bytes(self.world)
        self.state["freeBytes"] = shutil.disk_usage(self.world).free
        self.state["updatedUtc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        atomic_json(self.state_path, self.state)

    def health(self, status: str, message: str) -> None:
        try:
            value = json.loads(self.health_path.read_text("utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            value = {
                "schemaVersion": 1,
                "packVersion": "unknown",
                "protocolVersion": 1,
                "minecraftVersion": "1.21.1",
                "worldId": "drewcraft-production",
                "worldRevision": 1,
            }
        value.update(status=status, message=message)
        atomic_json(self.health_path, value)

    def rcon(self, *command: str) -> str:
        from rcon.source import Client
        password = self.password_path.read_text("utf-8").strip()
        with Client("127.0.0.1", self.args.rcon_port, passwd=password, timeout=10) as client:
            return client.run(*command)

    def idle_window(self) -> bool:
        """Return true only after the server has been empty for the grace period."""
        try:
            count = online_players(self.rcon("list"))
        except Exception as exc:
            self.health("unknown", f"Pregeneration waiting for player status: {exc}")
            return False
        if count is None:
            self.health("unknown", "Pregeneration waiting: could not parse player count")
            return False
        if count > 0:
            if not self.state.get("maintenancePaused"):
                for command in (("chunky", "pause"), ("dh", "pregen", "stop")):
                    try:
                        print(self.rcon(*command), flush=True)
                    except Exception as exc:
                        print(f"Could not pause {' '.join(command)}: {exc}", flush=True)
            self.save(maintenancePaused=True, idleSince=None, onlinePlayers=count)
            self.health("ready", f"Players online ({count}); pregeneration paused")
            return False
        now = time.time()
        idle_since = self.state.get("idleSince") or now
        self.save(idleSince=idle_since, onlinePlayers=0)
        if now - idle_since < self.args.idle_grace_seconds:
            self.health("ready", "Server empty; pregeneration starts after idle grace period")
            return False
        if self.state.get("maintenancePaused"):
            self.save(maintenancePaused=False)
            if self.state.get("phase") == "dh" and self.state.get("dhStarted"):
                # `/dh pregen stop` is intentionally used on player join.  A
                # fresh start is resumable because DH skips already indexed
                # LODs, and avoids treating the deliberate pause as completion.
                self.start_dh(self.state.get("dhTargetRadius", self.state["dhRadius"]))
        return True

    def write_boundary(self, radius: int) -> None:
        atomic_json(self.boundary_path, {
            "schemaVersion": 1,
            # The V1 world is intentionally not gameplay-bounded.  This file
            # remains as telemetry for the currently pregenerated frontier,
            # while players may explore beyond it and generate normally.
            "enabled": False,
            "dimension": "minecraft:overworld",
            "centerX": self.state["centerX"],
            "centerZ": self.state["centerZ"],
            "radiusBlocks": radius,
        })

    def configure_and_start(self, radius: int, *, resume: bool = False) -> None:
        commands = (
            ("chunky", "world", "minecraft:overworld"),
            ("chunky", "shape", "circle"),
            ("chunky", "center", str(self.state["centerX"]), str(self.state["centerZ"])),
            ("chunky", "radius", str(radius)),
            ("chunky", "start"),
        )
        self.write_boundary(radius)
        for command in commands:
            response = self.rcon(*command)
            print(response, flush=True)
        self.save(activeRadius=radius, **({} if resume else {"resumeAttempts": 0}))

    def start_dh(self, radius: int) -> None:
        radius_chunks = max(1, math.ceil(radius / 16))
        # DH's documented command surface calls this setting generation.mode;
        # PRE_EXISTING_ONLY prevents the LOD pass from creating a second copy
        # of terrain that Chunky owns.
        mode_response = self.rcon("dh", "config", "generation.mode", "PRE_EXISTING_ONLY")
        if any(word in mode_response.lower() for word in ("unknown", "invalid", "error")):
            raise RuntimeError(f"Distant Horizons refused PRE_EXISTING_ONLY mode: {mode_response}")
        print(mode_response, flush=True)
        response = self.rcon(
            "dh", "pregen", "start", "overworld",
            str(self.state["centerX"]), str(self.state["centerZ"]), str(radius_chunks),
        )
        print(response, flush=True)
        self.save(
            phase="dh",
            dhRadiusChunks=radius_chunks,
            dhTargetRadius=radius,
            dhMaintenanceActive=True,
            dhStarted=True,
            maintenancePaused=False,
        )

    def start_next_chunky_batch(self) -> bool:
        current = int(self.state.get("chunkyRadius", self.state["benchmarkRadius"]))
        target = int(self.state["activeRadius"])
        batch = max(16, int(self.args.generation_batch_blocks))
        next_radius = min(target, current + batch)
        if next_radius <= current:
            return False
        self.save(chunkyRadius=next_radius, phase="generate")
        self.configure_and_start(next_radius, resume=False)
        return True

    def start_dh_trailing_pass(self, *, final: bool = False) -> bool:
        chunky_radius = int(self.state.get("chunkyRadius", self.state["activeRadius"]))
        existing_dh = int(self.state.get("dhRadius", 0))
        lag = max(0, int(self.args.dh_lag_blocks))
        target = chunky_radius if final else max(0, chunky_radius - lag)
        target = max(existing_dh, target)
        if target <= existing_dh:
            return False
        self.save(phase="dh", phaseAfterDh="complete" if final else "generate")
        self.start_dh(target)
        return True

    def dh_finished(self) -> bool:
        try:
            response = self.rcon("dh", "pregen", "status")
        except Exception as exc:
            print(f"DH status unavailable: {exc}", flush=True)
            return False
        print(response, flush=True)
        if dh_task_running(response):
            return False
        # Once a DH task has been started, a status response reporting no task
        # means the bounded pass completed (or was already fully cached).
        return bool(self.state.get("dhStarted"))

    @staticmethod
    def running(progress: str) -> bool:
        return task_running(progress)

    @staticmethod
    def progress_percent(progress: str) -> float | None:
        match = re.search(r"\((\d+(?:\.\d+)?)%\)", progress)
        return float(match.group(1)) if match else None

    def stop_for_safety(self, reason: str) -> int:
        try:
            print(self.rcon("chunky", "pause"), flush=True)
            print(self.rcon("dh", "pregen", "stop"), flush=True)
        finally:
            self.save(phase="safety_paused", reason=reason)
            self.health("updating", f"Overworld pregeneration paused safely: {reason}")
        return 2

    def run(self) -> int:
        # Allow an operator to increase --target-bytes without deleting state.
        if self.args.target_bytes > self.state.get("targetBytes", 0):
            self.save(targetBytes=self.args.target_bytes)
            if self.state.get("phase") == "complete":
                self.save(phase="generate", completedBytes=None, dhStarted=False)
        self.write_boundary(self.state["activeRadius"])
        world_verified = False
        while True:
            if not self.idle_window():
                time.sleep(self.args.poll_seconds)
                continue
            if not world_verified:
                try:
                    print(verify_worldgen(self.world, pathlib.Path("/srv/drewcraft/persistent/server.properties")),
                          flush=True)
                    if self.state.get("phase") == "benchmark" and not self.state.get("centerSource"):
                        saved = read_nbt(self.world / "level.dat")["Data"]
                        self.save(centerX=int(saved["SpawnX"]), centerZ=int(saved["SpawnZ"]),
                                  centerSource="world-spawn")
                    world_verified = True
                except (OSError, KeyError, ValueError, RuntimeError) as exc:
                    self.health("failed", f"Pregeneration blocked: {exc}")
                    print(f"Pregeneration blocked: {exc}", flush=True)
                    return 2
            size = tree_bytes(self.world)
            free = shutil.disk_usage(self.world).free
            if size >= self.state["maximumBytes"]:
                return self.stop_for_safety("maximum world-size threshold reached")
            if free <= self.state["minimumFreeBytes"]:
                return self.stop_for_safety("minimum free-space reserve reached")

            if self.state["phase"] == "dh":
                if self.dh_finished():
                    dh_target = int(self.state.get("dhTargetRadius", self.state.get("dhRadius", 0)))
                    next_phase = self.state.get("phaseAfterDh", "complete")
                    self.save(
                        phase=next_phase,
                        dhRadius=max(int(self.state.get("dhRadius", 0)), dh_target),
                        dhMaintenanceActive=False,
                        lastDhMaintenanceEpoch=time.time(),
                        lastDhMaintenanceUtc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    )
                    if next_phase == "generate":
                        self.start_next_chunky_batch()
                    else:
                        self.health("ready", "Overworld and Distant Horizons pregeneration complete")
                time.sleep(self.args.poll_seconds)
                continue

            if self.state["phase"] == "complete":
                last = self.state.get("lastDhMaintenanceEpoch", 0)
                if time.time() - last >= self.args.dh_maintenance_interval_seconds:
                    self.save(
                        phase="dh", dhStarted=False,
                        lastDhMaintenanceEpoch=time.time(),
                    )
                    self.start_dh(self.state["activeRadius"])
                else:
                    self.health("ready", "World complete; waiting for the next DH maintenance window")
                time.sleep(self.args.poll_seconds)
                continue

            try:
                progress = self.rcon("chunky", "progress")
            except Exception as exc:
                print(f"RCON unavailable: {exc}", flush=True)
                time.sleep(self.args.poll_seconds)
                continue
            print(progress, flush=True)
            previous_progress = self.state.get("lastProgress", "")
            self.save(lastProgress=progress)
            if self.running(progress):
                time.sleep(self.args.poll_seconds)
                continue

            phase = self.state["phase"]
            previous_percent = self.progress_percent(previous_progress)
            if (phase in {"benchmark", "generate"}
                    and self.running(previous_progress)
                    and previous_percent is not None and previous_percent < 95.0
                    and self.state.get("resumeAttempts", 0) == 0):
                # Chunky 1.4.23 can report no resumable tasks after a clean server
                # restart even with continueOnRestart enabled. Re-submit the exact
                # same selection once; already generated chunks are skipped.
                self.save(resumeAttempts=1, resumeReason="Chunky task absent before 95%")
                self.configure_and_start(self.state.get("chunkyRadius", self.state["activeRadius"]), resume=True)
                time.sleep(self.args.poll_seconds)
                continue
            if phase == "benchmark":
                radius = min(
                    self.args.maximum_radius,
                    estimate_radius(
                        self.state["benchmarkRadius"], self.state["baselineBytes"],
                        size, self.state["targetBytes"],
                    ),
                )
                self.save(
                    phase="generate", benchmarkBytes=size, estimatedRadius=radius,
                    activeRadius=radius, chunkyRadius=self.state["benchmarkRadius"],
                )
                self.start_next_chunky_batch()
                time.sleep(self.args.poll_seconds)
                continue

            if (phase == "generate"
                    and size < int(self.state["targetBytes"] * 0.90)
                    and self.state.get("chunkyRadius", 0) >= self.state["activeRadius"]):
                if self.state["expansions"] >= self.args.maximum_expansions:
                    return self.stop_for_safety("target undershot after maximum automatic expansions")
                radius = min(
                    self.args.maximum_radius,
                    estimate_radius(
                        self.state["activeRadius"], self.state["baselineBytes"],
                        size, self.state["targetBytes"],
                    ),
                )
                if radius <= self.state["activeRadius"]:
                    return self.stop_for_safety("unable to calculate a larger safe radius")
                self.save(expansions=self.state["expansions"] + 1)
                self.save(activeRadius=radius)
                if not self.start_dh_trailing_pass(final=False):
                    self.start_next_chunky_batch()
                time.sleep(self.args.poll_seconds)
                continue

            # Chunky completed this batch. DH may trail by a fixed margin, then
            # Chunky advances to the next batch. The final pass reaches the
            # Chunky frontier exactly.
            final = (
                self.state.get("chunkyRadius", 0) >= self.state["activeRadius"]
                and size >= int(self.state["targetBytes"] * 0.90)
            )
            self.save(completedBytes=size, dhStarted=False, lastDhMaintenanceEpoch=time.time())
            if not self.start_dh_trailing_pass(final=final):
                if final:
                    self.save(phase="complete")
                else:
                    self.start_next_chunky_batch()
            time.sleep(self.args.poll_seconds)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--world", default="/srv/drewcraft/persistent/world")
    parser.add_argument("--state-file", default="/srv/drewcraft/state/pregen.json")
    parser.add_argument("--health-file", default="/srv/drewcraft/state/health.json")
    parser.add_argument("--password-file", default="/etc/drewcraft/rcon-password")
    parser.add_argument("--rcon-port", type=int, default=25575)
    parser.add_argument("--center-x", type=int, default=-5120)
    parser.add_argument("--center-z", type=int, default=5120)
    parser.add_argument("--baseline-bytes", type=int, required=True)
    parser.add_argument("--benchmark-radius", type=int, default=1024)
    parser.add_argument("--target-bytes", type=int, default=40_000_000_000)
    parser.add_argument("--maximum-bytes", type=int, default=45_000_000_000)
    parser.add_argument("--minimum-free-bytes", type=int, default=25_000_000_000)
    parser.add_argument("--maximum-radius", type=int, default=1_000_000)
    parser.add_argument("--maximum-expansions", type=int, default=3)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--generation-batch-blocks", type=int, default=1024)
    parser.add_argument("--dh-lag-blocks", type=int, default=512)
    parser.add_argument("--idle-grace-seconds", type=int, default=600)
    parser.add_argument(
        "--dh-maintenance-interval-seconds", type=int, default=3600,
        help="minimum idle interval between DH refresh passes after Chunky reaches the target",
    )
    return Controller(parser.parse_args()).run()


if __name__ == "__main__":
    raise SystemExit(main())
