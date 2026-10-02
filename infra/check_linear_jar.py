#!/usr/bin/env python3
"""Verify a safety-patched Linear server jar structurally (no JDK sensitivity).

Whole-jar SHA-256 pinning is unworkable: class bytecode varies across JDK
updates even for identical sources. Instead this checks what a rebuild must
preserve regardless of compiler:
  1. exact pinned upstream commit is enforced by the caller (rev-parse check);
  2. the jar entry set matches the tracked expectation for that commit+patch;
  3. every entry timestamp is the normalized reproducible-build stamp, proving
     the safety patch's reproducibility flags were active;
  4. the safety-patched classes are present (conversion-only hook + license).

Behavior is proven by the upstream unit tests, which run on these exact
classes in the same build before packaging. Per-file integrity of the
published release is hash-locked in release-manifest.json at pack time.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import zipfile

EXPECTED_ENTRIES = (
    pathlib.Path(__file__).resolve().parent / "linear-jar-entries.txt"
)

NORMALIZED_STAMP = (1980, 2, 1, 0, 0, 0)

REQUIRED_ENTRIES = (
    "com/memesgmm/linear/Linear.class",
    "com/memesgmm/linear/linear/MCAConverter.class",
    "com/memesgmm/linear/linear/LinearRegionFile.class",
    "META-INF/licenses/linear-MIT.txt",
)


def check(jar: pathlib.Path) -> dict:
    expected = EXPECTED_ENTRIES.read_text("utf-8").split()
    with zipfile.ZipFile(jar) as archive:
        infos = archive.infolist()
    actual = sorted(info.filename for info in infos)
    if actual != sorted(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise ValueError(
            f"Linear jar entry set differs from pinned commit+patch "
            f"(missing={missing} extra={extra})"
        )
    for info in infos:
        if info.date_time != NORMALIZED_STAMP:
            raise ValueError(
                f"Linear jar is not reproducibly timestamped: {info.filename} "
                f"has {info.date_time}; safety-patch flags may be inactive"
            )
        if info.file_size == 0 and not info.filename.endswith("/"):
            raise ValueError(f"Linear jar has an empty file: {info.filename}")
    for required in REQUIRED_ENTRIES:
        if required not in actual:
            raise ValueError(f"Linear jar lacks safety-patch proof: {required}")
    return {"entries": len(actual), "reproducible": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jar", type=pathlib.Path)
    args = parser.parse_args()
    result = check(args.jar)
    print(f"linear jar OK: {result['entries']} entries, timestamps normalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
