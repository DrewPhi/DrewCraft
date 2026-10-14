#!/usr/bin/env python3
"""Serve the tiny DrewCraft release health document to friend launchers."""
from __future__ import annotations

import argparse
import http.server
import json
import pathlib
import re
import shutil
import socket


class Handler(http.server.BaseHTTPRequestHandler):
    state_file: pathlib.Path
    server_host: str
    server_port: int
    lod_root = pathlib.Path('/srv/drewcraft/state/lod-public')

    def lod_file(self):
        name = self.path.removeprefix('/lod-export/')
        if not re.fullmatch(r'(publication\.json|[0-9a-f]{64}\.(sqlite|jsonl\.gz))', name):
            self.send_error(404)
            return
        root = self.lod_root.resolve()
        path = (root / name).resolve()
        if path.parent != root or not path.is_file():
            self.send_error(404)
            return
        with path.open('rb') as stream:
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(path.stat().st_size))
            self.send_header('Cache-Control', 'no-store' if name == 'publication.json' else 'public, max-age=31536000, immutable')
            self.end_headers()
            try:
                shutil.copyfileobj(stream, self.wfile, 256 * 1024)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def do_GET(self):
        if self.path.startswith('/lod-export/'):
            self.lod_file()
            return
        if self.path not in ("/health.json", "/health"):
            self.send_error(404)
            return
        try:
            payload = json.loads(self.state_file.read_text("utf-8"))
            if payload.get("status") == "ready":
                with socket.create_connection((self.server_host, self.server_port), timeout=1.0):
                    pass
            body = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            status = 200
        except Exception as exc:
            body = (json.dumps({"status": "unknown", "message": str(exc)}) + "\n").encode("utf-8")
            status = 503
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--state-file", default="/srv/drewcraft/state/health.json")
    p.add_argument("--bind", default="0.0.0.0")
    p.add_argument("--port", type=int, default=25566)
    p.add_argument("--server-host", default="127.0.0.1")
    p.add_argument("--server-port", type=int, default=25565)
    args = p.parse_args()
    Handler.state_file = pathlib.Path(args.state_file)
    Handler.server_host = args.server_host
    Handler.server_port = args.server_port
    server = http.server.ThreadingHTTPServer((args.bind, args.port), Handler)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
