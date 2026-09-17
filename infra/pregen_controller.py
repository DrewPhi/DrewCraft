#!/usr/bin/env python3
"""Drive a size-targeted, Overworld-only Chunky pregeneration safely."""
from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import re
import shutil
import tempfile
import time


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
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


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
            return json.loads(self.state_path.read_text("utf-8"))
        state = {
            "schemaVersion": 1,
            "phase": "benchmark",
            "centerX": self.args.center_x,
            "centerZ": self.args.center_z,
            "baselineBytes": self.args.baseline_bytes,
            "benchmarkRadius": self.args.benchmark_radius,
            "activeRadius": self.args.benchmark_radius,
            "targetBytes": self.args.target_bytes,
            "maximumBytes": self.args.maximum_bytes,
            "minimumFreeBytes": self.args.minimum_free_bytes,
            "expansions": 0,
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
        value = json.loads(self.health_path.read_text("utf-8"))
        value.update(status=status, message=message)
        atomic_json(self.health_path, value)

    def rcon(self, *command: str) -> str:
        from rcon.source import Client
        password = self.password_path.read_text("utf-8").strip()
        with Client("127.0.0.1", self.args.rcon_port, passwd=password, timeout=10) as client:
            return client.run(*command)

    def write_boundary(self, radius: int) -> None:
        atomic_json(self.boundary_path, {
            "schemaVersion": 1,
            "enabled": True,
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

    @staticmethod
    def running(progress: str) -> bool:
        return "Task running" in progress

    @staticmethod
    def progress_percent(progress: str) -> float | None:
        match = re.search(r"\((\d+(?:\.\d+)?)%\)", progress)
        return float(match.group(1)) if match else None

    def stop_for_safety(self, reason: str) -> int:
        try:
            print(self.rcon("chunky", "pause"), flush=True)
        finally:
            self.save(phase="safety_paused", reason=reason)
            self.health("updating", f"Overworld pregeneration paused safely: {reason}")
        return 2

    def run(self) -> int:
        if self.state["phase"] == "complete":
            return 0
        self.write_boundary(self.state["activeRadius"])
        self.health("updating", "Overworld pregeneration is running; Nether and End remain real-time")
        while True:
            size = tree_bytes(self.world)
            free = shutil.disk_usage(self.world).free
            if size >= self.state["maximumBytes"]:
                return self.stop_for_safety("maximum world-size threshold reached")
            if free <= self.state["minimumFreeBytes"]:
                return self.stop_for_safety("minimum free-space reserve reached")

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
                self.configure_and_start(self.state["activeRadius"], resume=True)
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
                self.save(phase="generate", benchmarkBytes=size, estimatedRadius=radius)
                self.configure_and_start(radius)
                time.sleep(self.args.poll_seconds)
                continue

            if phase == "generate" and size < int(self.state["targetBytes"] * 0.90):
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
                self.configure_and_start(radius)
                time.sleep(self.args.poll_seconds)
                continue

            self.save(phase="complete", completedBytes=size)
            gb = size / 1_000_000_000
            self.health("ready", f"Overworld pregeneration complete ({gb:.1f} GB); Nether and End remain real-time")
            print(f"Pregeneration complete: {size} bytes", flush=True)
            return 0


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
    parser.add_argument("--maximum-radius", type=int, default=16_384)
    parser.add_argument("--maximum-expansions", type=int, default=3)
    parser.add_argument("--poll-seconds", type=int, default=60)
    return Controller(parser.parse_args()).run()


if __name__ == "__main__":
    raise SystemExit(main())
