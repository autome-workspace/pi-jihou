"""Whitelisted template macros.

The template engine only evaluates these known macros plus user variables.
Arbitrary Python expressions are never executed.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta


def _format(value, fmt: str) -> str:
    if isinstance(value, datetime):
        mapping = {
            "YYYY": f"{value.year:04d}",
            "MM": f"{value.month:02d}",
            "DD": f"{value.day:02d}",
            "HH": f"{value.hour:02d}",
            "mm": f"{value.minute:02d}",
            "ss": f"{value.second:02d}",
        }
    else:
        mapping = {
            "YYYY": f"{value.year:04d}",
            "MM": f"{value.month:02d}",
            "DD": f"{value.day:02d}",
            "HH": "00",
            "mm": "00",
            "ss": "00",
        }
    result = fmt
    for token, replacement in mapping.items():
        result = result.replace(token, replacement)
    return result


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


class MacroRegistry:
    """Evaluates macro calls against the current application time."""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def today(self, fmt: str | None = None) -> str:
        d = self._now.date()
        return _format(d, fmt) if fmt else d.isoformat()

    def now(self, fmt: str | None = None) -> str:
        return _format(self._now, fmt) if fmt else self._now.isoformat(timespec="seconds")

    def year(self) -> int:
        return self._now.year

    def month(self) -> int:
        return self._now.month

    def day(self) -> int:
        return self._now.day

    def weekday(self) -> int:
        return self._now.weekday()  # Monday = 0

    def days_until(self, value) -> int:
        target = _as_date(value)
        return (target - self._now.date()).days

    def days_since(self, value) -> int:
        target = _as_date(value)
        return (self._now.date() - target).days


MACRO_NAMES = {
    "today",
    "now",
    "year",
    "month",
    "day",
    "weekday",
    "days_until",
    "days_since",
}
