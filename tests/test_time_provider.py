"""Tests for the application time provider."""

from datetime import datetime, timezone

from app.models.enums import NtpState
from app.time.time_provider import TimeProvider


def test_unsynchronized_falls_back_to_os_clock():
    provider = TimeProvider()
    assert provider.state == NtpState.UNSYNCHRONIZED
    before = datetime.now(timezone.utc)
    now = provider.now()
    after = datetime.now(timezone.utc)
    assert before <= now <= after


def test_apply_offset_sets_synchronized():
    provider = TimeProvider()
    provider.apply_offset(120.0, 5.0, "ntp.nict.jp")
    assert provider.state == NtpState.SYNCHRONIZED
    assert provider.offset_ms == 120.0
    assert provider.last_sync is not None


def test_mark_degraded():
    provider = TimeProvider()
    provider.apply_offset(0.0, 5.0, "time.cloudflare.com")
    provider.mark_degraded()
    assert provider.state == NtpState.DEGRADED


def test_mark_unsynchronized():
    provider = TimeProvider()
    provider.apply_offset(0.0, 5.0, "time.cloudflare.com")
    provider.mark_unsynchronized()
    assert provider.state == NtpState.UNSYNCHRONIZED
