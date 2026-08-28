"""Tests for voice cache key derivation."""

from app.voice.cache import compute_cache_key


def test_cache_key_is_stable():
    a = compute_cache_key(1, 0, {"speed": 1.0}, "こんにちは", "0.15.0")
    b = compute_cache_key(1, 0, {"speed": 1.0}, "こんにちは", "0.15.0")
    assert a == b


def test_cache_key_differs_by_text():
    a = compute_cache_key(1, 0, {}, "あ", "0.15.0")
    b = compute_cache_key(1, 0, {}, "い", "0.15.0")
    assert a != b


def test_cache_key_differs_by_speaker():
    a = compute_cache_key(1, 0, {}, "あ", "0.15.0")
    b = compute_cache_key(2, 0, {}, "あ", "0.15.0")
    assert a != b


def test_cache_key_differs_by_version():
    a = compute_cache_key(1, 0, {}, "あ", "0.15.0")
    b = compute_cache_key(1, 0, {}, "あ", "0.16.0")
    assert a != b
