"""Add DrewCraft to Minecraft's multiplayer list without losing user servers."""
from __future__ import annotations

from dataclasses import dataclass
import gzip
import os
from pathlib import Path
import struct
import tempfile


@dataclass
class Tag:
    kind: int
    value: object


class Reader:
    def __init__(self, data: bytes):
        self.data = memoryview(data)
        self.pos = 0

    def take(self, n: int) -> bytes:
        if n < 0 or self.pos + n > len(self.data):
            raise ValueError("truncated servers.dat")
        value = self.data[self.pos:self.pos + n].tobytes()
        self.pos += n
        return value

    def number(self, fmt: str):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self) -> str:
        return self.take(self.number(">H")).decode("utf-8")

    def tag(self, kind: int) -> Tag:
        if kind in (1, 2, 3, 4, 5, 6):
            return Tag(kind, self.number({1: ">b", 2: ">h", 3: ">i", 4: ">q", 5: ">f", 6: ">d"}[kind]))
        if kind in (7, 11, 12):
            count = self.number(">i")
            return Tag(kind, self.take(count * {7: 1, 11: 4, 12: 8}[kind]))
        if kind == 8:
            return Tag(kind, self.string())
        if kind == 9:
            element_kind = self.number(">B")
            count = self.number(">i")
            if count < 0 or count > 100_000:
                raise ValueError("invalid servers.dat list length")
            return Tag(kind, (element_kind, [self.tag(element_kind) for _ in range(count)]))
        if kind == 10:
            children = {}
            while True:
                child_kind = self.number(">B")
                if child_kind == 0:
                    break
                name = self.string()
                children[name] = self.tag(child_kind)
            return Tag(kind, children)
        raise ValueError(f"unsupported servers.dat tag: {kind}")


def _string(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return struct.pack(">H", len(encoded)) + encoded


def _write(tag: Tag) -> bytes:
    kind, value = tag.kind, tag.value
    if kind in (1, 2, 3, 4, 5, 6):
        return struct.pack({1: ">b", 2: ">h", 3: ">i", 4: ">q", 5: ">f", 6: ">d"}[kind], value)
    if kind in (7, 11, 12):
        width = {7: 1, 11: 4, 12: 8}[kind]
        return struct.pack(">i", len(value) // width) + value
    if kind == 8:
        return _string(value)
    if kind == 9:
        element_kind, members = value
        return struct.pack(">Bi", element_kind, len(members)) + b"".join(_write(member) for member in members)
    if kind == 10:
        return b"".join(bytes([child.kind]) + _string(name) + _write(child)
                        for name, child in value.items()) + b"\x00"
    raise ValueError(f"unsupported servers.dat tag: {kind}")


def _load(path: Path) -> tuple[Tag, bool]:
    if not path.is_file():
        return Tag(10, {"servers": Tag(9, (10, []))}), False
    data = path.read_bytes()
    compressed = data.startswith(b"\x1f\x8b")
    if compressed:
        data = gzip.decompress(data)
    reader = Reader(data)
    if reader.number(">B") != 10:
        raise ValueError("servers.dat root is not a compound")
    reader.string()
    root = reader.tag(10)
    if reader.pos != len(data):
        raise ValueError("servers.dat has trailing bytes")
    return root, compressed


def ensure_server(path: Path, address: str, name: str = "DrewCraft") -> bool:
    """Return True only if a new entry was added. Never replace existing entries."""
    if not address or not isinstance(address, str):
        return False
    root, compressed = _load(path)
    servers = root.value.get("servers")
    if servers is None:
        servers = Tag(9, (10, []))
        root.value["servers"] = servers
    if servers.kind != 9 or servers.value[0] != 10:
        raise ValueError("servers.dat has an unexpected servers list")
    members = servers.value[1]
    if any(item.kind == 10 and item.value.get("ip", Tag(8, "")).value == address
           for item in members):
        return False
    members.append(Tag(10, {"name": Tag(8, name), "ip": Tag(8, address)}))
    raw = b"\x0a\x00\x00" + _write(root)
    if compressed:
        raw = gzip.compress(raw, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".servers-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(raw)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return True
