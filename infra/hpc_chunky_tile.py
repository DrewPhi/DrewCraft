#!/usr/bin/env python3
"""Generate one Chunky tile on an HPC worker using the exact production stack.

Fresh seed-identical world, RCON-driven Chunky, timed phases for ETA math.
Stdlib + python rcon package only. Exits nonzero (no partial credit) if any
phase fails; prints a single RESULT JSON line for the driver to collect.
"""
import argparse
import json
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path


def rcon(password: str, port: int, *command: str, timeout: int = 30) -> str:
    from rcon.source import Client
    with Client("127.0.0.1", port, passwd=password, timeout=timeout) as client:
        return client.run(*command)


def checked(password: str, port: int, *command: str) -> str:
    response = rcon(password, port, *command)
    if not response.strip() or re.search(
            r"unknown|incorrect|invalid|exception|failed|error", response, re.I):
        raise RuntimeError(f"command failed {command}: {response.strip()[:200]}")
    return response


def wait_for(predicate, seconds: int, description: str) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(15)
    raise TimeoutError(description)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--java", type=Path, required=True)
    ap.add_argument("--models", type=Path, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--level-type", required=True)
    ap.add_argument("--center", nargs=2, type=int, required=True)
    ap.add_argument("--radius", type=int, required=True)
    ap.add_argument("--rcon-port", type=int, default=25580)
    ap.add_argument("--server-port", type=int, default=25565)
    ap.add_argument("--boot-timeout", type=int, default=1200)
    ap.add_argument("--gen-timeout", type=int, default=21600)
    args = ap.parse_args()

    work = args.work
    world = work / "world"
    result: dict = {"status": "RUNNING", "startedUnix": time.time(),
                    "center": args.center, "radius": args.radius,
                    "comparisonStatus": "NOT_RUN", "dhPregenerationRequested": False}
    proc = None
    try:
        if work.exists():
            raise RuntimeError(f"work dir exists; refusing overwrite: {work}")
        eula = args.app / "eula.txt"
        if not eula.is_file() or not re.search(r"(?m)^eula=true\s*$", eula.read_text()):
            raise RuntimeError("Bundle must contain the already accepted production eula.txt")
        if not args.models.is_dir() or not any(args.models.glob("*.onnx")):
            raise RuntimeError("Pinned model directory missing or has no ONNX models")
        (work / "mods").mkdir(parents=True)
        for name in sorted((args.app / "mods").glob("*.jar")):
            shutil.copy2(name, work / "mods" / name.name)
        for name in ("config", "datapacks", "libraries", "defaultconfigs", "drewcraft-integration"):
            src = args.app / name
            if src.is_dir():
                shutil.copytree(src, work / name, symlinks=True)
        for name in ("run.sh", "user_jvm_args.txt", "eula.txt"):
            src = args.app / name
            if src.is_file():
                shutil.copy2(src, work / name)
        shutil.copytree(args.models, work / "terrain-diffusion-models")
        td_config = work / "config/terrain-diffusion-mc.properties"
        if td_config.is_file():
            lines = [line for line in td_config.read_text().splitlines()
                     if not line.startswith("explorer.address=")]
            td_config.write_text("\n".join(lines + ["explorer.address=127.0.0.1"]) + "\n")
        secret = secrets.token_urlsafe(32)
        (work / "server.properties").write_text(
            "\n".join([
                "server-ip=127.0.0.1",
                f"server-port={args.server_port}",
                "online-mode=false",
                "white-list=false",
                "enable-rcon=true",
                "rcon.ip=127.0.0.1",
                f"rcon.port={args.rcon_port}",
                f"rcon.password={secret}",
                "level-name=world",
                f"level-seed={args.seed}",
                f"level-type={args.level_type}",
                "sync-chunk-writes=true",
                "enable-query=false",
            ]) + "\n")
        (work / "server.properties").chmod(0o600)
        (work / "logs").mkdir(exist_ok=True)
        (world / "datapacks").mkdir(parents=True)
        for managed in (work / "datapacks").glob("*"):
            if managed.is_dir() and (managed / "pack.mcmeta").is_file():
                shutil.copytree(managed, world / "datapacks" / managed.name)

        java = args.java / "bin/java"
        log = open(work / "runner.log", "w")
        t0 = time.monotonic()
        proc = subprocess.Popen(
            [str(java), "@user_jvm_args.txt",
             "@libraries/net/neoforged/neoforge/21.1.250/unix_args.txt", "nogui"],
            cwd=work, stdout=log, stderr=subprocess.STDOUT)
        ready = {"ok": False}

        def is_ready() -> bool:
            if proc.poll() is not None:
                raise RuntimeError(f"HPC server exited during boot: {proc.returncode}; see runner.log")
            try:
                response = rcon(secret, args.rcon_port, "list")
                ready["ok"] = bool(re.search(r"There are \d+ ", response))
                return ready["ok"]
            except Exception:
                return False

        wait_for(is_ready, args.boot_timeout, "HPC server boot timed out")
        result["bootSeconds"] = round(time.monotonic() - t0, 1)
        for command in [("world", "minecraft:overworld"), ("shape", "square"),
                        ("center", str(args.center[0]), str(args.center[1])),
                        ("radius", str(args.radius))]:
            checked(secret, args.rcon_port, "chunky", *command)
        offset = (work / "logs/latest.log").stat().st_size
        response = checked(secret, args.rcon_port, "chunky", "start")
        if "task was already started for this world" in response.lower():
            response = checked(secret, args.rcon_port, "chunky", "confirm")
        if "started" not in response.lower():
            raise RuntimeError("Chunky did not start: " + response[:200])

        t1 = time.monotonic()

        def finished() -> bool:
            if proc.poll() is not None:
                raise RuntimeError(f"HPC server exited during generation: {proc.returncode}")
            with open(work / "logs/latest.log", "rb") as stream:
                stream.seek(offset)
                tail = stream.read().decode("utf-8", "replace")[-8000:]
            if re.search(r"MixinApplyError|InvalidMixinException|Exception generating", tail):
                raise RuntimeError("Chunky runtime failure; see logs/latest.log")
            return bool(re.search(
                r"Task finished for (?:minecraft:)?overworld.*\(100(?:\.0+)?%\)", tail))

        wait_for(finished, args.gen_timeout, "Chunky tile did not finish")
        result["genSeconds"] = round(time.monotonic() - t1, 1)
        began = time.monotonic()
        response = checked(secret, args.rcon_port, "save-all", "flush")
        if "Saved the game" not in response:
            raise RuntimeError("save-all not acknowledged")
        result["saveSeconds"] = round(time.monotonic() - began, 1)
        region = list((world / "region").glob("r.*.*.linear")) + \
            list((world / "region").glob("r.*.*.mca"))
        result["regionFiles"] = len(region)
        result["status"] = "PASS"
    except BaseException as error:  # noqa: BLE001 - report then exit nonzero
        result["status"] = "FAILED"
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        if proc is not None and proc.poll() is None:
            try:
                rcon(secret, args.rcon_port, "stop")
            except Exception:
                pass
            try:
                proc.wait(timeout=180)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
                result["status"] = "FAILED"
                result["shutdownError"] = "Server required forced termination; output is not accepted"
        result["finishedUnix"] = time.time()
        line = "HPC_RESULT " + json.dumps(result, sort_keys=True)
        if work.is_dir():
            (work / "result.json").write_text(json.dumps(result, sort_keys=True) + "\n")
            with (work / "runner.log").open("a") as stream:
                stream.write(line + "\n")
        print(line, flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
