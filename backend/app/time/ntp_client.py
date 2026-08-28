"""Minimal SNTP client (RFC 4330) implemented on top of the standard library.

No external NTP library is required. Queries an NTP server over UDP/123 and
returns the estimated clock offset and round-trip latency.
"""

from __future__ import annotations

import socket
import struct
import time

NTP_EPOCH = 2_208_988_800  # seconds between 1900-01-01 and 1970-01-01
NTP_PACKET_SIZE = 48

# LI=0, VN=3, Mode=3 (client)
_CLIENT_PACKET_HEADER = 0x1B


def _to_ntp(timestamp: float) -> tuple[int, int]:
    seconds = int(timestamp + NTP_EPOCH)
    fraction = int((timestamp + NTP_EPOCH - seconds) * (2**32))
    return seconds, fraction


def _from_ntp(seconds: int, fraction: int) -> float:
    return seconds - NTP_EPOCH + (fraction / (2**32))


def _parse_timestamp(data: bytes, offset: int) -> float:
    seconds, fraction = struct.unpack_from("!II", data, offset)
    return _from_ntp(seconds, fraction)


def query(server: str, port: int = 123, timeout: float = 5.0) -> tuple[float, float]:
    """Query an NTP server.

    Returns a tuple of ``(offset_seconds, latency_seconds)`` where a positive
    offset means the server is ahead of the local wall clock.
    """
    packet = bytearray(NTP_PACKET_SIZE)
    packet[0] = _CLIENT_PACKET_HEADER

    t1 = time.time()
    t1_seconds, t1_fraction = _to_ntp(t1)
    struct.pack_into("!II", packet, 40, t1_seconds, t1_fraction)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(packet, (server, port))
        data, _ = sock.recvfrom(1024)
    t4 = time.time()

    t2 = _parse_timestamp(data, 32)
    t3 = _parse_timestamp(data, 40)

    offset = ((t2 - t1) + (t3 - t4)) / 2.0
    latency = (t4 - t1) - (t3 - t2)
    if latency < 0:
        latency = 0.0
    return offset, latency


async def query_async(
    server: str, port: int = 123, timeout: float = 5.0
) -> tuple[float, float]:
    """Async wrapper around :func:`query` (run in a thread)."""
    import asyncio

    return await asyncio.to_thread(query, server, port, timeout)
