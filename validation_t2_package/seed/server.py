"""Synthetic training device. Loopback only; use invented passwords."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

DEFAULT = dict(connection="serial", device="COM1", host="127.0.0.1", port="502", auth="none", password="")


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/settings":
            self.reply(200, json.loads(STATE.read_text()) if STATE.exists() else DEFAULT)
        elif self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(Path(__file__).with_name("ui.html").read_bytes())
        else:
            self.reply(404, {"message": "Not found"})

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if self.path == "/api/reset":
            STATE.write_text(json.dumps(DEFAULT))
            return self.reply(200, DEFAULT)
        if self.path != "/api/settings":
            return self.reply(404, {"message": "Not found"})
        error = None
        if data.get("connection") not in ("tcp", "serial") or data.get("auth") not in ("none", "password"):
            error = "Invalid selection"
        elif data["connection"] == "tcp":
            try:
                port = int(data.get("port", ""))
                maximum = 65534 if VARIANT == "bad-boundary" else 65535
                if not 1 <= port <= maximum:
                    error = "Port must be 1..65535"
            except ValueError:
                error = "Port must be 1..65535"
            if not data.get("host", "").strip():
                error = "Host required"
        elif not data.get("device", "").strip():
            error = "Device required"
        if data.get("auth") == "password" and not data.get("password"):
            error = "Password required"
        if error:
            return self.reply(400, {"message": error})
        if VARIANT != "no-persist":
            STATE.write_text(json.dumps({key: data.get(key, "") for key in DEFAULT}))
        self.reply(200, {"message": "Saved"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--variant", choices=("correct", "no-persist", "bad-boundary"), default="correct")
    parser.add_argument("--state", type=Path, default=Path("state.json"))
    args = parser.parse_args()
    STATE, VARIANT = args.state, args.variant
    print(f"Training UI: http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
