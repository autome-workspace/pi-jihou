"""Schedule service: CRUD with rule handling."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Schedule, ScheduleRule
from app.schemas.schedule import ScheduleCreate, ScheduleRuleBase, ScheduleUpdate


def _apply_rules(schedule: Schedule, rules: list[ScheduleRuleBase] | None) -> None:
    if rules is None:
        return
    schedule.rules = []
    for rule in rules:
        if isinstance(rule, dict):
            rule = ScheduleRuleBase(**rule)
        schedule.rules.append(
            ScheduleRule(
                rule_type=rule.rule_type.value,
                time=rule.time,
                start_time=rule.start_time,
                end_time=rule.end_time,
                interval_minutes=rule.interval_minutes,
                days_of_week=rule.days_of_week,
                specific_date=rule.specific_date,
                cron_expression=rule.cron_expression,
            )
        )


def create_schedule(db: Session, data: ScheduleCreate) -> Schedule:
    schedule = Schedule(
        name=data.name,
        enabled=data.enabled,
        volume=data.volume,
        priority=data.priority,
        conflict_policy=data.conflict_policy.value,
        audio_type=data.audio_type.value,
        audio_file_id=data.audio_file_id,
        voice_template_id=data.voice_template_id,
    )
    _apply_rules(schedule, data.rules)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def update_schedule(db: Session, schedule: Schedule, data: ScheduleUpdate) -> Schedule:
    updates = data.model_dump(exclude_unset=True, exclude={"rules"})
    rules = data.rules
    for field, value in updates.items():
        if field in {"conflict_policy", "audio_type"} and value is not None:
            value = value.value
        setattr(schedule, field, value)
    _apply_rules(schedule, rules)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule
