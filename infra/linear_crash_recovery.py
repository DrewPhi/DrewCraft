"""Interrupt and resume Linear conversion on a disposable copy only.

The production server and world are never stopped or modified.  The test copies
the pinned Anvil baseline to an isolated world path, SIGKILLs the converter
while an Anvil source and its in-progress Linear target coexist, resumes the
conversion-only startup, and byte-compares every converted chunk payload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path("/srv/drewcraft")
TEST = ROOT / "linear-verification"
BASELINE = TEST / "baseline/persistent/world"
RUNTIME = TEST / "runtime"
EVIDENCE_ROOT = TEST / "crash-drills"
JAVA = "/opt/drewcraft/java/bin/java"
UNIT_PREFIX = "drewcraft-linear-crash"
MIN_FREE = 25_000_000_000
BOOT_ARGS = ["@user_jvm_args.txt", "@libraries/net/neoforged/neoforge/21.1.250/unix_args.txt", "nogui"]

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rcon.source import Client
from region_inventory import linear_payloads
from verify_region_conversion import anvil_payloads


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=check, text=True, capture_output=True)


def disk_free() -> int:
    return shutil.disk_usage(TEST).free


def safe_unit_state(unit: str) -> str:
    result = run(["systemctl", "show", unit, "-p", "ActiveState", "--value"], check=False)
    state = result.stdout.strip()
    return state or "not-found"


def unit_log(unit: str) -> str:
    result = run(["journalctl", "-u", unit, "--no-pager", "-n", "80"], check=False)
    return result.stdout


def production_empty() -> str:
    password = Path("/etc/drewcraft/rcon-password").read_text().strip()
    with Client("127.0.0.1", 25575, passwd=password, timeout=10) as client:
        response = client.run("list")
    if "There are 0 of a max of" not in response:
        raise RuntimeError(f"Production not confirmed empty; drill deferred: {response!r}")
    return response


def runtime_properties() -> tuple[Path, str]:
    path = RUNTIME / "server.properties"
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("Isolated server.properties is missing or symlinked")
    original = path.read_text()
    props = dict(line.split("=", 1) for line in original.splitlines()
                 if "=" in line and not line.startswith("#"))
    if (props.get("server-ip") != "127.0.0.1" or props.get("server-port") != "25585"
            or props.get("rcon.port") != "25586" or props.get("rcon.ip") != "127.0.0.1"):
        raise RuntimeError("Refusing an isolated runtime with non-local ports")
    if props.get("level-name") != "world":
        raise RuntimeError("Unexpected test-runtime world selection")
    return path, original


def configure_world(path: Path, original: str, name: str) -> None:
    lines = [line for line in original.splitlines() if not line.startswith("level-name=")]
    path.write_text("\n".join(lines + [f"level-name={name}"]) + "\n")


def launch_converter(unit: str) -> None:
    result = run([
        "systemd-run", "--unit=" + unit,
        "--description=Disposable interrupted Linear conversion drill",
        "--property=User=drewcraft", "--property=WorkingDirectory=" + str(RUNTIME),
        "--property=Nice=15", "--property=CPUQuota=200%", "--property=MemoryMax=16G",
        "--property=IOWeight=25", "--property=ProtectSystem=strict",
        "--property=ReadWritePaths=" + str(RUNTIME), "--property=PrivateTmp=yes",
        "--property=KillSignal=SIGINT", "--property=TimeoutStopSec=120",
        "--setenv=JAVA_TOOL_OPTIONS=-Ddrewcraft.linear.convertOnly=true",
        JAVA, *BOOT_ARGS,
    ])
    print(result.stdout.strip(), flush=True)


def wait_for_state(unit: str, deadline: float) -> str:
    while time.monotonic() < deadline:
        state = safe_unit_state(unit)
        if state in ("inactive", "failed", "deactivating"):
            return state
        time.sleep(1)
    raise TimeoutError(f"Timed out waiting for {unit}; state={safe_unit_state(unit)}")


def kill_unit(unit: str, signal: str) -> None:
    run(["systemctl", "kill", "--kill-who=main", "--signal=" + signal, unit], check=False)


def stop_unit(unit: str) -> None:
    if safe_unit_state(unit) not in ("inactive", "failed", "not-found"):
        kill_unit(unit, "SIGKILL")
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline and safe_unit_state(unit) not in ("inactive", "failed"):
            time.sleep(1)


def region_counts(baseline: Path, converted: Path) -> dict:
    regions = chunks = 0
    for source in sorted(baseline.rglob("r.*.*.mca")):
        expected = anvil_payloads(source)
        target = converted / source.relative_to(baseline).with_suffix(".linear")
        if not expected and not target.exists():
            continue
        actual = linear_payloads(target)
        if actual != expected:
            raise ValueError(f"Recovered conversion payload mismatch: {source.relative_to(baseline)}")
        regions += 1
        chunks += len(expected)
    anvil_left = [path for path in converted.rglob("*.mca") if path.stat().st_size]
    external_left = list(converted.rglob("*.mcc"))
    if anvil_left or external_left:
        raise ValueError(f"Conversion did not finish; .mca={len(anvil_left)} .mcc={len(external_left)}")
    return {"verifiedRegionFiles": regions, "verifiedChunkPayloads": chunks}


def drill(run_id: str) -> dict:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,24}", run_id):
        raise ValueError("Invalid run id")
    evidence = EVIDENCE_ROOT / run_id
    world_name = "linear-crash-" + run_id
    disposable_world = RUNTIME / world_name
    first_unit = UNIT_PREFIX + "-" + run_id + "-first"
    resume_unit = UNIT_PREFIX + "-" + run_id + "-resume"
    if evidence.exists() or disposable_world.exists():
        raise RuntimeError("Evidence or test world already exists; refusing overwrite")
    if safe_unit_state("drewcraft-linear-test.service") not in ("inactive", "failed", "not-found"):
        raise RuntimeError("Isolated test server is running; refusing concurrent test")
    result = {"status": "RUNNING", "scope": "disposable pinned Anvil baseline only",
              "runId": run_id, "startedUnix": time.time(), "productionWorldTouched": False}
    evidence.mkdir(parents=True)
    properties_path = None
    original_properties = None
    try:
        result["productionPlayers"] = production_empty()
        properties_path, original_properties = runtime_properties()
        source_bytes = sum(p.stat().st_size for p in BASELINE.rglob("*") if p.is_file())
        if not (BASELINE / "level.dat").is_file():
            raise RuntimeError("Pinned baseline world is missing level.dat")
        if disk_free() < source_bytes + MIN_FREE:
            raise RuntimeError(f"Insufficient room for disposable copy plus 25 GB reserve: need {source_bytes + MIN_FREE:,}")
        if any(p.is_symlink() for p in BASELINE.rglob("*")):
            raise RuntimeError("Pinned baseline contains a symlink; refusing copy")
        result["baselineBytes"] = source_bytes
        result["freeBytesBeforeCopy"] = disk_free()
        configure_world(properties_path, original_properties, world_name)
        shutil.copytree(BASELINE, disposable_world)
        run(["chown", "-R", "drewcraft:drewcraft", str(disposable_world)])
        if disk_free() < MIN_FREE:
            raise RuntimeError("25 GB free-space reserve reached after disposable world copy")
        result["freeBytesAfterCopy"] = disk_free()
        existing_anvil = sorted(disposable_world.rglob("r.*.*.mca"))
        if not existing_anvil:
            raise RuntimeError("Baseline copy has no Anvil regions to exercise")
        largest = max(existing_anvil, key=lambda p: p.stat().st_size)
        expected_source_hash = hashlib.sha256(largest.read_bytes()).hexdigest()
        result["interruptionTarget"] = str(largest.relative_to(disposable_world))
        result["interruptionSourceSha256"] = expected_source_hash

        launch_converter(first_unit)
        started = time.monotonic()
        deadline = started + 3600
        target = largest.with_suffix(".linear")
        while time.monotonic() < deadline:
            if disk_free() < MIN_FREE:
                raise RuntimeError("25 GB reserve reached while converting; stopping test converter")
            if target.exists() and largest.exists():
                kill_unit(first_unit, "SIGSTOP")
                time.sleep(0.2)
                if target.exists() and largest.exists():
                    result["interruptedAtUnix"] = time.time()
                    result["partialTargetBytes"] = target.stat().st_size
                    result["sourceStillPresentAtInterrupt"] = True
                    kill_unit(first_unit, "SIGKILL")
                    wait_for_state(first_unit, time.monotonic() + 120)
                    break
                kill_unit(first_unit, "SIGCONT")
            state = safe_unit_state(first_unit)
            if state in ("inactive", "failed"):
                if (disposable_world / ".linear-conversion-complete").is_file():
                    raise RuntimeError("Converter completed before an interruption could be injected")
                raise RuntimeError("Converter exited before the interruption point; inspect its journal")
            time.sleep(0.05)
        else:
            raise TimeoutError("No in-flight Anvil/Linear pair observed within one hour")

        if not largest.exists() or not target.exists():
            raise RuntimeError("Interrupted converter did not preserve both source and target")
        if hashlib.sha256(largest.read_bytes()).hexdigest() != expected_source_hash:
            raise RuntimeError("SIGKILL changed the retained Anvil source")
        result["sourcePreservedAfterKill"] = True
        launch_converter(resume_unit)
        state = wait_for_state(resume_unit, time.monotonic() + 7200)
        log = unit_log(resume_unit)
        (evidence / "resume-journal.txt").write_text(log)
        marker = disposable_world / ".linear-conversion-complete"
        if not marker.is_file() or "DREWCRAFT_CONVERSION_ONLY_COMPLETE" not in log:
            raise RuntimeError(f"Resumed conversion did not emit completion marker; state={state}")
        result.update(region_counts(BASELINE, disposable_world))
        result["conversionResume"] = "PASS"
        result["completionMarker"] = marker.read_text().strip()
        result["status"] = "PASS"
        return result
    except BaseException as error:
        result["status"] = "FAILED"
        result["error"] = f"{type(error).__name__}: {error}"
        result["preservedFailureWorld"] = str(disposable_world) if disposable_world.exists() else None
        result["firstConverterJournal"] = unit_log(first_unit)
        result["resumeConverterJournal"] = unit_log(resume_unit)
        traceback.print_exc()
        raise
    finally:
        stop_unit(first_unit)
        stop_unit(resume_unit)
        if properties_path and original_properties is not None:
            try:
                properties_path.write_text(original_properties)
            except OSError as cleanup_error:
                result["status"] = "FAILED_CLEANUP"
                result["propertiesRestoreError"] = str(cleanup_error)
        result["finishedUnix"] = time.time()
        result["freeBytesAtFinish"] = disk_free()
        result["pregenerationControllerState"] = safe_unit_state("drewcraft-pregen.service")
        if result["status"] == "PASS" and disposable_world.exists():
            try:
                shutil.rmtree(disposable_world)
                result["disposableWorldCleaned"] = True
            except OSError as cleanup_error:
                result["status"] = "FAILED_CLEANUP"
                result["cleanupError"] = str(cleanup_error)
        (evidence / "result.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    print(json.dumps(drill(args.run_id), indent=2), flush=True)
