import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "mock_bridge_last_run.json"


class Handler(BaseHTTPRequestHandler):
    def _write_json(self, status, payload):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._write_json(200, {
                "ok": True,
                "service": "smart-trapper-mock-bridge",
                "version": "0.1.0",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            return

        self._write_json(404, {"ok": False, "message": "Not found"})

    def do_POST(self):
        if self.path != "/run":
            self._write_json(404, {"ok": False, "message": "Not found"})
            return

        try:
          length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
          length = 0

        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            self._write_json(400, {"ok": False, "message": f"Invalid JSON: {exc}"})
            return

        snapshot = {
            "receivedAt": datetime.utcnow().isoformat() + "Z",
            "payload": payload
        }
        LOG_FILE.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

        self._write_json(200, {
            "ok": True,
            "message": "Mock bridge received run payload",
            "savedTo": str(LOG_FILE)
        })


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8765), Handler)
    print("Mock Smart Trapper bridge listening on http://127.0.0.1:8765")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
