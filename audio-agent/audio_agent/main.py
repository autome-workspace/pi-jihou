"""Audio Agent HTTP server (localhost only).

Implemented with the Python standard library only (no third-party
dependencies), so the agent can be installed on the Raspberry Pi without
pip/PyPI access.
"""

from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__
from .devices import enumerate_devices, is_mock
from .player import playback_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# Default: loopback only (never exposed to the network). When the backend runs
# in a container, set AUDIO_AGENT_BIND=0.0.0.0 so host.docker.internal can
# reach it, and protect the port with a firewall.
BIND_HOST = os.environ.get("AUDIO_AGENT_BIND", "127.0.0.1")
BIND_PORT = int(os.environ.get("AUDIO_AGENT_PORT", "8031"))


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    def _route(self):
        return self.path.split("?", 1)[0]

    def do_GET(self) -> None:  # noqa: N802
        path = self._route()
        if path == "/health":
            self._send_json({"status": "ok", "mock": is_mock()})
        elif path == "/devices":
            self._send_json(enumerate_devices())
        elif path == "/devices/current":
            current = next((d for d in enumerate_devices() if d.get("default")), None)
            self._send_json(current)
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        path = self._route()
        data = self._read_json()
        try:
            if path == "/play":
                self._send_json(
                    playback_manager.play(data.get("path", ""), data.get("device_id"))
                )
            elif path == "/stop":
                self._send_json(playback_manager.stop())
            elif path == "/test":
                self._send_json(playback_manager.test(data.get("id", "")))
            elif path == "/volume":
                self._send_json(playback_manager.set_volume(data.get("volume", 80)))
            else:
                self._send_json({"error": "not found"}, 404)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"status": "error", "error": str(exc)}, 500)

    def do_PUT(self) -> None:  # noqa: N802
        path = self._route()
        data = self._read_json()
        if path == "/devices/current":
            self._send_json({"id": data.get("id"), "status": "set"})
        else:
            self._send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):  # noqa: A003
        logger.info("%s - %s", self.address_string(), fmt % args)


def main() -> None:
    server = ThreadingHTTPServer((BIND_HOST, BIND_PORT), Handler)
    server.daemon_threads = True
    logger.info("Audio Agent v%s listening on %s:%s", __version__, BIND_HOST, BIND_PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
