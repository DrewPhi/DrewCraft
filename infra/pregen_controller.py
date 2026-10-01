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
from region_inventory import linear_header


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
    return (task_running(response) or "generated radius:" in text) and "not running" not in text and "no pre-generation" not in text


def checked_dh_response(response: str) -> str:
    if not response.strip() or any(word in response.lower() for word in (
        "unknown", "invalid", "error", "incorrect", "failed", "exception",
    )):
        raise RuntimeError(f"Distant Horizons command failed: {response}")
    return response


def region_fingerprints(world: pathlib.Path) -> dict[str, list[int]]:
    """Cheap change detection; only inspect the Overworld's saved region files."""
    result = {}
    coordinates = set()
    for path in (world / "region").glob("r.*.*.*"):
        if not re.fullmatch(r"r\.-?\d+\.-?\d+\.(mca|linear)", path.name):
            continue
        stat = path.stat()
        coordinate = region_coordinates(path.name)
        if coordinate in coordinates:
            raise RuntimeError(f'Duplicate Anvil/Linear region at {coordinate}; conversion requires review')
        coordinates.add(coordinate)
        if path.suffix == '.linear':
            if linear_header(path)[0]:
                result[path.name] = [stat.st_mtime_ns, stat.st_size]
        elif stat.st_size >= 8192:
            result[path.name] = [stat.st_mtime_ns, stat.st_size]
    return result


def region_coordinates(name: str) -> tuple[int, int]:
    parts = name.split(".")
    return int(parts[1]), int(parts[2])


def existing_world_radius(regions: dict, center_x: int, center_z: int) -> int:
    """Enclose all saved regions, including newly explored terrain, with margin."""
    distance = 0
    for name in regions:
        rx, rz = region_coordinates(name)
        distance = max(distance, abs(rx * 512 - center_x),
                       abs((rx + 1) * 512 - center_x), abs(rz * 512 - center_z),
                       abs((rz + 1) * 512 - center_z))
    return max(512, math.ceil((distance + 64) / 16) * 16)


def changed_region_jobs(regions: dict, baseline: dict, center_x: int,
                        center_z: int) -> list[dict]:
    """Group dirty regions into 2048-block squares, nearest spawn first."""
    groups: dict[tuple[int, int], dict] = {}
    for name, fingerprint in regions.items():
        if baseline.get(name) == fingerprint:
            continue
        rx, rz = region_coordinates(name)
        groups.setdefault((rx // 4, rz // 4), {})[name] = fingerprint
    jobs = [
        {"kind": "changed_regions", "centerX": gx * 2048 + 1024,
         "centerZ": gz * 2048 + 1024, "radius": 1088, "regions": changed}
        for (gx, gz), changed in groups.items()
    ]
    return sorted(jobs, key=lambda job: (
        (job["centerX"] - center_x) ** 2 + (job["centerZ"] - center_z) ** 2,
        job["centerX"], job["centerZ"],
    ))


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

    def health(self, status: str, message: str, *, joinable: bool = False) -> None:
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
        # Keep health metadata aligned with the release actually serving the
        # world.  A stale previous-release health file must not block clients
        # after a successful server rollout.
        manifest_path = pathlib.Path("/srv/drewcraft/current/.drewcraft-release-manifest.json")
        try:
            manifest = json.loads(manifest_path.read_text("utf-8"))
            value.update(
                packVersion=manifest.get("packVersion", value.get("packVersion")),
                protocolVersion=manifest.get("protocolVersion", value.get("protocolVersion", 1)),
            )
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        value.update(status=status, message=message, joinable=joinable)
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
            self.health("ready", f"Players online ({count}); pregeneration paused", joinable=True)
            return False
        now = time.time()
        idle_since = self.state.get("idleSince") or now
        self.save(idleSince=idle_since, onlinePlayers=0)
        if now - idle_since < self.args.idle_grace_seconds:
            self.health("ready", "Server empty; pregeneration starts after idle grace period", joinable=True)
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
        enabled = bool(self.state.get("enforcePregenBoundary"))
        generated_radius = radius
        if enabled:
            # Never expose an in-progress selection. Leave space for the
            # client's full-chunk window (view distance 10) outside the player.
            generated_radius = int(self.state.get("continuousCompletedRadius", 0))
            radius = generated_radius - int(self.state.get("boundaryBufferBlocks", 320))
            if radius <= 8:
                raise RuntimeError("No completed terrain circle available for exploration boundary")
        atomic_json(self.boundary_path, {
            "schemaVersion": 1,
            "enabled": enabled,
            "dimension": "minecraft:overworld",
            "centerX": self.state["centerX"],
            "centerZ": self.state["centerZ"],
            "radiusBlocks": radius,
            "generatedRadiusBlocks": generated_radius,
            "bufferBlocks": generated_radius - radius if enabled else 0,
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
        radius_chunks = max(32, math.ceil(radius / 16))
        job = self.state.get("dhActiveJob") or {}
        center_x = job.get("centerX", self.state["centerX"])
        center_z = job.get("centerZ", self.state["centerZ"])
        # DH 3.3.1: disable surface prediction and read actual saved chunks only.
        for setting, value in (("generation.plan", "CHUNKS_ONLY"),
                               ("generation.chunkMode", "PRE_EXISTING_ONLY")):
            print(checked_dh_response(self.rcon("dh", "config", setting, value)), flush=True)
        log = pathlib.Path("/srv/drewcraft/logs/latest.log")
        stat = log.stat()
        self.save(dhLogInode=stat.st_ino, dhLogOffset=stat.st_size)
        response = checked_dh_response(self.rcon(
            "dh", "pregen", "start", "overworld",
            str(center_x), str(center_z), str(radius_chunks),
        ))
        if "Starting pregen" not in response:
            raise RuntimeError(f"DH did not acknowledge pregen start: {response}")
        print(response, flush=True)
        self.save(
            phase="dh",
            dhRadiusChunks=radius_chunks,
            dhTargetRadius=radius,
            dhMaintenanceActive=True,
            dhStarted=True,
            maintenancePaused=False,
            dhJobCenterX=center_x,
            dhJobCenterZ=center_z,
        )

    def maintain_dh(self) -> bool:
        """One catch-up sweep, then persistent jobs for new/changed regions only."""
        pending = list(self.state.get("dhPendingJobs") or [])
        if not pending:
            now = time.time()
            interval = self.args.dh_change_check_seconds
            if now - self.state.get("dhLastRegionCheckEpoch", 0) < interval:
                return False
            regions = region_fingerprints(self.world)
            if not regions:
                self.save(dhLastRegionCheckEpoch=now)
                return False
            database = self.world / "data" / "DistantHorizons.sqlite"
            stat = database.stat() if database.exists() else None
            identity = [stat.st_dev, stat.st_ino] if stat else None
            baseline = self.state.get("dhRegionBaseline")
            radius = existing_world_radius(regions, self.state["centerX"], self.state["centerZ"])
            if baseline is None or identity != self.state.get("dhDatabaseIdentity"):
                if radius > self.args.maximum_radius:
                    raise RuntimeError("Existing Overworld DH bounds exceed maximum radius")
                pending = [{"kind": "catchup", "centerX": self.state["centerX"],
                            "centerZ": self.state["centerZ"], "radius": radius,
                            "regions": regions, "databaseIdentity": identity}]
            else:
                pending = changed_region_jobs(regions, baseline,
                                              self.state["centerX"], self.state["centerZ"])
            self.save(dhPendingJobs=pending, dhLastRegionCheckEpoch=now,
                      dhExistingWorldRadius=radius,
                      dhChangeTracking="region_mtime_ns_and_size")
        if not pending:
            return False
        job = pending.pop(0)
        # Snapshot before work: any changes during the pass remain dirty later.
        self.save(dhPendingJobs=pending, dhActiveJob=job, dhStarted=False,
                  phase="dh", phaseAfterDh="complete")
        self.start_dh(job["radius"])
        return True

    def finish_dh_job(self) -> None:
        job = self.state["dhActiveJob"]
        baseline = {} if job["kind"] == "catchup" else dict(self.state.get("dhRegionBaseline") or {})
        baseline.update(job["regions"])
        updates = {}
        if job["kind"] == "catchup":
            database = self.world / "data" / "DistantHorizons.sqlite"
            stat = database.stat()
            updates.update(dhDatabaseIdentity=[stat.st_dev, stat.st_ino],
                           dhRadius=job["radius"], dhOnlyRadius=job["radius"])
        self.save(phase="complete", dhActiveJob=None, dhStarted=False,
                  dhRegionBaseline=baseline, dhMaintenanceActive=False,
                  dhCompletedJobs=self.state.get("dhCompletedJobs", 0) + 1,
                  lastDhMaintenanceEpoch=time.time(),
                  lastDhMaintenanceUtc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                  **updates)

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

    def continuous_chunky_step(self, size: int) -> None:
        """Expand small circles, requiring real task completion before advancing."""
        log = pathlib.Path("/srv/drewcraft/logs/latest.log")
        if self.state["phase"] == "continuous_chunky":
            response = self.rcon("chunky", "progress")
            if self.running(response):
                self.save(lastProgress=response)
                return
            stat = log.stat()
            messages = ""
            if (stat.st_ino == self.state.get("chunkyLogInode")
                    and stat.st_size >= self.state.get("chunkyLogOffset", 0)):
                with log.open("rb") as stream:
                    stream.seek(self.state["chunkyLogOffset"])
                    messages = stream.read().decode("utf-8", errors="replace")
            if re.search(r"Task finished for (?:minecraft:)?overworld\..*\(100(?:\.0+)?%\)", messages):
                self.save(continuousCompletedRadius=self.state["continuousTargetRadius"],
                          phase="complete", dhLastRegionCheckEpoch=0)
                self.write_boundary(self.state["continuousCompletedRadius"])
                return
            # Pause/restart is not completion. Resume the saved selection.
            continued = self.rcon("chunky", "continue")
            print(continued, flush=True)
            if "no tasks" in continued.lower():
                self.start_continuous_chunky(self.state["continuousTargetRadius"])
            return
        # DH always catches up before another terrain batch; storage target
        # stops expansion, but incremental LOD maintenance continues.
        if self.maintain_dh():
            return
        if size >= self.state["targetBytes"]:
            self.health("ready", "Terrain size target reached; DH maintenance continues", joinable=True)
            return
        radius = int(self.state["continuousCompletedRadius"]) + max(16, self.args.generation_batch_blocks)
        if radius > self.args.maximum_radius:
            self.health("ready", "Terrain radius safety limit reached; DH maintenance continues", joinable=True)
            return
        self.start_continuous_chunky(radius)

    def start_continuous_chunky(self, radius: int) -> None:
        log = pathlib.Path("/srv/drewcraft/logs/latest.log")
        stat = log.stat()
        self.save(phase="continuous_chunky", continuousTargetRadius=radius,
                  chunkyLogInode=stat.st_ino, chunkyLogOffset=stat.st_size)
        for command in (("chunky", "world", "minecraft:overworld"),
                        ("chunky", "shape", "circle"),
                        ("chunky", "center", str(self.state["centerX"]), str(self.state["centerZ"])),
                        ("chunky", "radius", str(radius))):
            response = self.rcon(*command)
            if any(word in response.lower() for word in ("unknown", "invalid", "error", "incorrect", "failed")):
                raise RuntimeError(f"Chunky selection failed: {response}")
        response = self.rcon("chunky", "start")
        print(response, flush=True)
        if "task started" not in response.lower():
            raise RuntimeError(f"Chunky did not acknowledge new task: {response}")
        self.save(activeRadius=radius)
        self.write_boundary(radius)

    def pause_at_size_target(self, size: int) -> bool:
        """Enforce the total-world budget during jobs, not just between batches."""
        if not self.state.get("continuousChunky") or size < self.state["targetBytes"]:
            return False
        if self.state["phase"] != "size_paused":
            print(self.rcon("chunky", "pause"), flush=True)
            print(self.rcon("dh", "pregen", "stop"), flush=True)
            self.save(sizePausedFromPhase=self.state["phase"], phase="size_paused",
                      dhStarted=False, reason="world storage target reached")
        self.health("ready", "World storage target reached; background generation paused", joinable=True)
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
        checked_dh_response(response)
        # An absent task is not proof of success (restart/cancel/failure).
        log = pathlib.Path("/srv/drewcraft/logs/latest.log")
        stat = log.stat()
        if (stat.st_ino == self.state.get("dhLogInode")
                and stat.st_size >= self.state.get("dhLogOffset", 0)):
            with log.open("rb") as stream:
                stream.seek(self.state.get("dhLogOffset", stat.st_size))
                messages = stream.read().decode("utf-8", errors="replace")
            if "Pregen is complete" in messages:
                return True
        if response.strip() == "Pregen is not running":
            self.start_dh(self.state["dhTargetRadius"])
        return False

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
            # A target undershoot is an administrative pause, not a server
            # deployment.  Minecraft remains joinable while an operator
            # decides whether to resume with a larger expansion budget.
            status = "ready" if reason == "target undershot after maximum automatic expansions" else "updating"
            self.health(status, f"Overworld pregeneration paused safely: {reason}", joinable=(status == "ready"))
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
            self.health("updating", "Pregeneration active; server remains joinable", joinable=True)
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

            if self.pause_at_size_target(size):
                time.sleep(self.args.poll_seconds)
                continue
            if self.state["phase"] == "size_paused":
                # Raising the budget resumes the interrupted job, not a new
                # optimistic completed-radius checkpoint.
                self.save(phase=self.state.get("sizePausedFromPhase", "complete"), reason=None)

            if self.state["phase"] == "safety_paused":
                self.health("ready", "Pregeneration paused at operator/safety limit", joinable=True)
                time.sleep(self.args.poll_seconds)
                continue

            if self.state.get("continuousChunky") and self.state["phase"] in {"complete", "continuous_chunky"}:
                self.continuous_chunky_step(size)
                time.sleep(self.args.poll_seconds)
                continue

            if self.state.get("dhOnly") and self.state["phase"] not in {"dh", "complete"}:
                return self.stop_for_safety("DH-only mode refuses terrain expansion")

            if self.state["phase"] == "dh":
                if not self.state.get("dhStarted"):
                    self.start_dh(self.state["dhTargetRadius"])
                if self.dh_finished():
                    if self.state.get("dhActiveJob"):
                        self.finish_dh_job()
                        self.health("ready", "DH job complete; checking remaining changed terrain", joinable=True)
                        time.sleep(self.args.poll_seconds)
                        continue
                    dh_target = int(self.state.get("dhTargetRadius", self.state.get("dhRadius", 0)))
                    next_phase = self.state.get("phaseAfterDh", "complete")
                    self.save(
                        phase=next_phase,
                        dhRadius=max(int(self.state.get("dhRadius", 0)), dh_target),
                        dhMaintenanceActive=False,
                        lastDhMaintenanceEpoch=time.time(),
                        lastDhMaintenanceUtc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    )
                    if next_phase == "generate" and not self.state.get("dhOnly"):
                        self.start_next_chunky_batch()
                    else:
                        self.health("ready", "DH pass complete for existing Overworld; terrain expansion paused", joinable=True)
                time.sleep(self.args.poll_seconds)
                continue

            if self.state["phase"] == "complete":
                try:
                    started = self.maintain_dh()
                except (OSError, RuntimeError) as exc:
                    print(f"DH incremental maintenance deferred: {exc}", flush=True)
                    self.health("ready", f"DH maintenance waiting: {exc}", joinable=True)
                else:
                    if not started:
                        self.health("ready", "DH idle: waiting for new or changed saved Overworld terrain", joinable=True)
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
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--generation-batch-blocks", type=int, default=1024)
    parser.add_argument("--dh-lag-blocks", type=int, default=512)
    parser.add_argument("--idle-grace-seconds", type=int, default=600)
    parser.add_argument("--dh-change-check-seconds", type=int, default=60,
                        help="idle interval between cheap saved-region change checks")
    parser.add_argument(
        "--dh-maintenance-interval-seconds", type=int, default=3600,
        help="legacy option accepted for existing service units; DH now refreshes changed regions only",
    )
    return Controller(parser.parse_args()).run()


if __name__ == "__main__":
    raise SystemExit(main())
