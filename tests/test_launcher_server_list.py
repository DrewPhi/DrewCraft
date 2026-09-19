from __future__ import annotations

import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "launcher"))
from drewcraft_server_list import Reader, Tag, _write, ensure_server  # noqa: E402


def test_server_list_adds_once_and_preserves_player_entries():
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "servers.dat"
        assert ensure_server(path, "150.136.96.174:25565")
        original = path.read_bytes()
        assert not ensure_server(path, "150.136.96.174:25565")
        assert path.read_bytes() == original
        reader = Reader(original)
        assert reader.number(">B") == 10
        reader.string()
        root = reader.tag(10)
        members = root.value["servers"].value[1]
        assert members[0].value["ip"].value == "150.136.96.174:25565"
        members.insert(0, Tag(10, {"name": Tag(8, "My other server"), "ip": Tag(8, "example.invalid")}))
        path.write_bytes(b"\x0a\x00\x00" + _write(root))
        assert not ensure_server(path, "150.136.96.174:25565")
        assert b"My other server" in path.read_bytes()
