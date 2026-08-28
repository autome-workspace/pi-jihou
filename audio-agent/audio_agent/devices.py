"""Audio device enumeration.

Devices are identified by persistent identifiers (PipeWire node name, ALSA card
id, or description), never by card index alone, so USB hotplug does not break
selection. In mock mode a fixed set of fake devices is returned.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess

logger = logging.getLogger(__name__)

MOCK_DEVICES = [
    {"id": "mock-analog", "name": "Mock Analog", "description": "Built-in analog (mock)", "default": True},
    {"id": "mock-hdmi", "name": "Mock HDMI", "description": "HDMI output (mock)", "default": False},
    {"id": "mock-usb-dac", "name": "Mock USB DAC", "description": "USB Audio DAC (mock)", "default": False},
]


def is_mock() -> bool:
    return os.environ.get("AUDIO_AGENT_MOCK", "").lower() in {"1", "true", "yes"}


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        logger.warning("%s failed: %s", cmd[0], result.stderr.strip())
    return result.stdout


def _from_wpctl() -> list[dict]:
    if not shutil.which("wpctl"):
        logger.info("wpctl not found")
        return []
    out = _run(["wpctl", "status"])
    if not out:
        return []

    devices: list[dict] = []
    in_sinks = False
    for raw in out.splitlines():
        line = raw.strip()
        # Section headers look like " ├─ Sinks:" (with box-drawing prefix), so
        # match by substring rather than startswith.
        if "Sinks:" in line:
            in_sinks = True
            continue
        if in_sinks and any(
            token in line
            for token in (
                "Sources:",
                "Sink endpoints:",
                "Source endpoints:",
                "Filters:",
                "Streams:",
                "Devices:",
            )
        ):
            in_sinks = False
            continue
        if not in_sinks or not line:
            continue

        # Example line: "│  *   57. Built-in Audio Stereo               [vol: 1.00]"
        is_default = "*" in line
        body = line.lstrip("*│ ")
        if "." not in body:
            continue
        _, rest = body.split(".", 1)
        name = rest.split("[", 1)[0].strip()
        if not name:
            continue
        devices.append(
            {
                "id": name,
                "name": name,
                "description": name,
                "default": is_default,
            }
        )

    if not any(d["default"] for d in devices) and devices:
        devices[0]["default"] = True
    return devices


def _from_pactl() -> list[dict]:
    if not shutil.which("pactl"):
        return []
    out = _run(["pactl", "list", "short", "sinks"])
    devices: list[dict] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        # index \t name \t description
        node = parts[1].strip()
        description = parts[2].strip() if len(parts) > 2 else node
        devices.append(
            {"id": node, "name": description, "description": node, "default": len(devices) == 0}
        )
    return devices


def enumerate_devices() -> list[dict]:
    if is_mock():
        return MOCK_DEVICES
    devices = _from_wpctl() or _from_pactl()
    if not devices:
        logger.warning(
            "No audio sinks found (wpctl/pactl empty or unavailable). "
            "Check that PipeWire is running and accessible to this process."
        )
        devices = [
            {
                "id": "default",
                "name": "Default output",
                "description": "PipeWire default sink",
                "default": True,
            }
        ]
    if not any(d["default"] for d in devices):
        devices[0]["default"] = True
    return devices
