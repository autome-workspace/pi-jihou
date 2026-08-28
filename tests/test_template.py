"""Tests for the safe template engine and macros."""

from datetime import datetime

import pytest

from app.voice.template import TemplateError, evaluate


def test_plain_text_passes_through():
    assert evaluate("hello world", {}, datetime(2026, 1, 1, 0, 0)) == "hello world"


def test_variable_expansion():
    variables = {"event_name": "NHKロボコン"}
    result = evaluate("{{ event_name }}です", variables, datetime(2026, 1, 1))
    assert result == "NHKロボコンです"


def test_today_macro():
    result = evaluate("{{ today() }}", {}, datetime(2026, 9, 15, 10, 0))
    assert result == "2026-09-15"


def test_today_with_format():
    result = evaluate('{{ today("YYYY/MM/DD") }}', {}, datetime(2026, 9, 15))
    assert result == "2026/09/15"


def test_now_with_format():
    result = evaluate('{{ now("HH:mm") }}', {}, datetime(2026, 9, 15, 17, 30))
    assert result == "17:30"


def test_days_until():
    result = evaluate('{{ days_until("2026-09-15") }}', {}, datetime(2026, 8, 28))
    assert result == "18"


def test_days_until_variable():
    variables = {"event_date": "2026-09-15"}
    result = evaluate("{{ days_until(event_date) }}", variables, datetime(2026, 8, 28))
    assert result == "18"


def test_unknown_variable_raises():
    with pytest.raises(TemplateError):
        evaluate("{{ nope }}", {}, datetime(2026, 1, 1))


def test_disallowed_call_raises():
    with pytest.raises(TemplateError):
        evaluate("{{ __import__('os') }}", {}, datetime(2026, 1, 1))


def test_disallowed_macro_raises():
    with pytest.raises(TemplateError):
        evaluate("{{ system('rm -rf /') }}", {}, datetime(2026, 1, 1))
