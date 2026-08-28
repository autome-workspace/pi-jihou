"""Raspberry Pi Audio Agent.

Host-side audio output service. Listens on 127.0.0.1:8031 and talks to
PipeWire/ALSA directly, decoupling audio device access from the Dockerized
backend.
"""

__version__ = "0.1.0"
