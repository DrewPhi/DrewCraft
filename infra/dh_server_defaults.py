"""Persist DH 3.3.1 saved-chunk generation policy without replacing other settings."""
import argparse
import os
from pathlib import Path
import re
import tempfile
import tomllib


def apply(path: Path) -> bool:
    text = path.read_text() if path.is_file() else ""
    tomllib.loads(text)  # Refuse malformed configuration before writing.
    lines = text.splitlines()
    header = next((i for i, line in enumerate(lines)
                   if line.strip() == "[common.worldGenerator]"), None)
    if header is None:
        lines += ["", "[common.worldGenerator]"]
        header = len(lines) - 1
    for key, value in (("generatorPlan", "CHUNKS_ONLY"),
                       ("chunkGeneratorMode", "PRE_EXISTING_ONLY")):
        end = next((i for i in range(header + 1, len(lines))
                    if lines[i].strip().startswith("[")), len(lines))
        existing = next((i for i in range(header + 1, end)
                         if re.match(rf"\s*{key}\s*=", lines[i])), None)
        replacement = f'{key} = "{value}"'
        if existing is None:
            lines.insert(header + 1, replacement)
        else:
            lines[existing] = replacement
    updated = "\n".join(lines) + "\n"
    tomllib.loads(updated)
    if updated == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    stat = path.stat() if path.exists() else None
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        if stat:
            os.chmod(name, stat.st_mode & 0o777)
            if os.geteuid() == 0:
                os.chown(name, stat.st_uid, stat.st_gid)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print("DH saved-chunk policy:", "updated" if apply(args.config) else "already applied")
