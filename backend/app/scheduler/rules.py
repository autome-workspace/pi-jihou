"""Recurrence rule evaluation.

Given a schedule rule and a reference time, compute the next occurrence. Rules
are evaluated against application time (UTC).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from app.models import ScheduleRule, ScheduleType


def next_occurrence(rule: ScheduleRule, after: datetime) -> datetime | None:
    """Return the next occurrence of *rule* strictly after *after*."""
    rule_type = ScheduleType(rule.rule_type)

    if rule_type == ScheduleType.ONCE or rule_type == ScheduleType.DATE:
        return _next_on_date(rule.specific_date, rule.time, after)

    if rule_type == ScheduleType.DAILY:
        return _next_daily(rule.time, after)

    if rule_type == ScheduleType.WEEKDAYS:
        return _next_weekdays(rule.time, after)

    if rule_type == ScheduleType.WEEKLY:
        days = set(rule.days_of_week or [])
        return _next_weekly(days, rule.time, after)

    if rule_type == ScheduleType.CRON:
        return _next_cron(rule.cron_expression or "", after)

    return None


def _next_on_date(specific: date | None, at: time | None, after: datetime) -> datetime | None:
    if specific is None:
        return None
    t = at or time(0, 0, 0)
    candidate = datetime.combine(specific, t)
    if candidate.tzinfo is None:
        candidate = candidate.replace(tzinfo=after.tzinfo)
    return candidate if candidate > after else None


def _next_daily(at: time | None, after: datetime) -> datetime | None:
    t = at or time(0, 0, 0)
    candidate = after.replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
    if candidate <= after:
        candidate += timedelta(days=1)
    return candidate


def _next_weekdays(at: time | None, after: datetime) -> datetime | None:
    t = at or time(0, 0, 0)
    candidate = after.replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
    for _ in range(8):
        if candidate > after and candidate.weekday() < 5:
            return candidate
        candidate += timedelta(days=1)
    return None


def _next_weekly(days: set[int], at: time | None, after: datetime) -> datetime | None:
    if not days:
        return None
    t = at or time(0, 0, 0)
    candidate = after.replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
    for _ in range(8):
        if candidate > after and candidate.weekday() in days:
            return candidate
        candidate += timedelta(days=1)
    return None


# --- Minimal 5-field cron (minute hour day-of-month month day-of-week) ---

def _parse_cron_field(field: str, minimum: int, maximum: int) -> set[int]:
    values: set[int] = set()
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, step_str = part.split("/", 1)
            step = int(step_str)
        if part == "*":
            start, end = minimum, maximum
        elif "-" in part:
            start_str, end_str = part.split("-", 1)
            start, end = int(start_str), int(end_str)
        else:
            start = end = int(part)
        values.update(range(start, end + 1, step))
    return values


def _next_cron(expression: str, after: datetime) -> datetime | None:
    fields = expression.split()
    if len(fields) != 5:
        return None
    minutes = _parse_cron_field(fields[0], 0, 59)
    hours = _parse_cron_field(fields[1], 0, 23)
    dom = _parse_cron_field(fields[2], 1, 31)
    months = _parse_cron_field(fields[3], 1, 12)
    dow = _parse_cron_field(fields[4], 0, 6)

    candidate = (after + timedelta(minutes=1)).replace(second=0, microsecond=0)
    for _ in range(366 * 24 * 60):
        if candidate.month not in months:
            candidate = candidate.replace(day=1, hour=0, minute=0) + timedelta(days=32)
            candidate = candidate.replace(day=1)
            continue
        if (
            candidate.minute in minutes
            and candidate.hour in hours
            and candidate.day in dom
            and candidate.weekday() in dow
        ):
            return candidate
        candidate += timedelta(minutes=1)
    return None
