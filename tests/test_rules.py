"""Tests for schedule recurrence rule evaluation."""

from datetime import datetime, time

from app.models import ScheduleRule
from app.scheduler.rules import next_occurrence


def _rule(rule_type, *, at=None, days=None, specific_date=None, cron=None):
    return ScheduleRule(
        rule_type=rule_type,
        time=at,
        days_of_week=days,
        specific_date=specific_date,
        cron_expression=cron,
    )


def test_daily_next_same_day():
    rule = _rule("daily", at=time(12, 0, 0))
    after = datetime(2026, 8, 28, 11, 0)
    assert next_occurrence(rule, after) == datetime(2026, 8, 28, 12, 0)


def test_daily_next_rolls_to_next_day():
    rule = _rule("daily", at=time(12, 0, 0))
    after = datetime(2026, 8, 28, 13, 0)
    assert next_occurrence(rule, after) == datetime(2026, 8, 29, 12, 0)


def test_weekdays_skips_weekend():
    rule = _rule("weekdays", at=time(9, 0, 0))
    after = datetime(2026, 8, 28, 20, 0)  # Friday
    # Saturday 8/29 and Sunday 8/30 are skipped -> Monday 8/31
    assert next_occurrence(rule, after) == datetime(2026, 8, 31, 9, 0)


def test_weekly_specific_days():
    rule = _rule("weekly", at=time(8, 0, 0), days=[2, 4])  # Wed, Fri
    after = datetime(2026, 8, 28, 7, 0)  # Friday
    assert next_occurrence(rule, after) == datetime(2026, 8, 28, 8, 0)


def test_date_past_returns_none():
    rule = _rule("date", at=time(10, 0, 0), specific_date=datetime(2026, 1, 1).date())
    after = datetime(2026, 8, 28)
    assert next_occurrence(rule, after) is None


def test_date_future():
    rule = _rule("date", at=time(10, 0, 0), specific_date=datetime(2026, 9, 15).date())
    after = datetime(2026, 8, 28)
    assert next_occurrence(rule, after) == datetime(2026, 9, 15, 10, 0)


def test_cron_every_minute():
    rule = _rule("cron", cron="* * * * *")
    after = datetime(2026, 8, 28, 12, 0, 30)
    assert next_occurrence(rule, after) == datetime(2026, 8, 28, 12, 1)


def test_cron_daily_at_time():
    rule = _rule("cron", cron="0 9 * * *")
    after = datetime(2026, 8, 28, 8, 0)
    assert next_occurrence(rule, after) == datetime(2026, 8, 28, 9, 0)


def _interval(start, end, mins, days=None):
    return ScheduleRule(
        rule_type="interval",
        start_time=start,
        end_time=end,
        interval_minutes=mins,
        days_of_week=days,
    )


def test_interval_first_fire_at_start():
    rule = _interval(time(9, 0), time(17, 0), 10)
    after = datetime(2026, 8, 28, 8, 30)
    assert next_occurrence(rule, after) == datetime(2026, 8, 28, 9, 0)


def test_interval_next_step_within_window():
    rule = _interval(time(9, 0), time(17, 0), 10)
    after = datetime(2026, 8, 28, 9, 25)
    assert next_occurrence(rule, after) == datetime(2026, 8, 28, 9, 30)


def test_interval_after_window_rolls_next_day():
    rule = _interval(time(9, 0), time(17, 0), 10)
    after = datetime(2026, 8, 28, 18, 0)
    assert next_occurrence(rule, after) == datetime(2026, 8, 29, 9, 0)


def test_interval_last_fire_at_or_before_end():
    rule = _interval(time(9, 0), time(9, 25), 10)
    # fires at 09:00, 09:10, 09:20 (09:30 would exceed end)
    after = datetime(2026, 8, 28, 9, 15)
    assert next_occurrence(rule, after) == datetime(2026, 8, 28, 9, 20)


def test_interval_skips_non_applicable_days():
    rule = _interval(time(9, 0), time(17, 0), 10, days=[0, 1, 2])  # Mon-Wed
    after = datetime(2026, 8, 28, 18, 0)  # Friday 8/28
    # Skip Fri, Sat, Sun, Mon -> skip to Tuesday? next applicable day > Fri is Mon 8/31
    assert next_occurrence(rule, after) == datetime(2026, 8, 31, 9, 0)


def test_interval_zero_fires_once_at_start():
    # interval=0 (continuous): fire once at window start; executor loops.
    rule = _interval(time(9, 0), time(17, 0), 0)
    after = datetime(2026, 8, 28, 8, 30)
    assert next_occurrence(rule, after) == datetime(2026, 8, 28, 9, 0)


def test_interval_zero_mid_window_rolls_next_day():
    # With interval=0 the schedule already fired at 09:00 and is looping; if the
    # scheduler wakes mid-window it should not re-fire, but roll to next day.
    rule = _interval(time(9, 0), time(17, 0), 0)
    after = datetime(2026, 8, 28, 10, 0)
    assert next_occurrence(rule, after) == datetime(2026, 8, 29, 9, 0)
