#!/usr/bin/env python3
"""Serve the tiny DrewCraft release health document to friend launchers."""
from __future__ import annotations

import argparse
import http.server
import json
import pathlib


class Handler(http.server.BaseHTTPRequestHandler):
    state_file: pathlib.Path

    def do_GET(self):
        if self.path not in ("/health.json", "/health"):
            self.send_error(404)
            return
        try:
            payload = json.loads(self.state_file.read_text("utf-8"))
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
    args = p.parse_args()
    Handler.state_file = pathlib.Path(args.state_file)
    server = http.server.ThreadingHTTPServer((args.bind, args.port), Handler)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
