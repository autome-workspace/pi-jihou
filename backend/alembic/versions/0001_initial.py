"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.String(2048), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "audio_files",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("original_path", sa.String(1024), nullable=False),
        sa.Column("playback_path", sa.String(1024), nullable=False, server_default=""),
        sa.Column("format", sa.String(16), nullable=False, server_default=""),
        sa.Column("sample_rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("channels", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bit_depth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "voice_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("template_text", sa.String(4096), nullable=False, server_default=""),
        sa.Column("speaker_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("style_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("speed", sa.Float(), nullable=False, server_default="1"),
        sa.Column("pitch", sa.Float(), nullable=False, server_default="0"),
        sa.Column("intonation", sa.Float(), nullable=False, server_default="1"),
        sa.Column("volume", sa.Float(), nullable=False, server_default="1"),
        sa.Column("pre_silence_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("post_silence_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generation_strategy", sa.String(32), nullable=False, server_default="before_playback"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "voice_variables",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("value_type", sa.String(16), nullable=False),
        sa.Column("value", sa.String(1024), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "voice_cache",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cache_key", sa.String(64), nullable=False),
        sa.Column("wav_path", sa.String(1024), nullable=False),
        sa.Column("speaker_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("style_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("expanded_text", sa.String(4096), nullable=False, server_default=""),
        sa.Column("voicevox_version", sa.String(64), nullable=False, server_default=""),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_voice_cache_cache_key", "voice_cache", ["cache_key"], unique=True)

    op.create_table(
        "schedules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("volume", sa.Integer(), nullable=False, server_default="80"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("conflict_policy", sa.String(16), nullable=False, server_default="queue"),
        sa.Column("audio_type", sa.String(16), nullable=False, server_default="file"),
        sa.Column("audio_file_id", sa.String(36), sa.ForeignKey("audio_files.id"), nullable=True),
        sa.Column("voice_template_id", sa.String(36), sa.ForeignKey("voice_templates.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "schedule_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("schedule_id", sa.String(36), sa.ForeignKey("schedules.id"), nullable=False),
        sa.Column("rule_type", sa.String(16), nullable=False, server_default="daily"),
        sa.Column("time", sa.Time(), nullable=True),
        sa.Column("days_of_week", sa.JSON(), nullable=True),
        sa.Column("specific_date", sa.Date(), nullable=True),
        sa.Column("cron_expression", sa.String(128), nullable=True),
    )

    op.create_table(
        "schedule_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("schedule_id", sa.String(36), sa.ForeignKey("schedules.id"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.Column("result", sa.String(16), nullable=False, server_default="pending"),
    )

    op.create_table(
        "playback_queue",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("schedule_id", sa.String(36), sa.ForeignKey("schedules.id"), nullable=True),
        sa.Column("audio_file_id", sa.String(36), nullable=True),
        sa.Column("voice_cache_id", sa.String(36), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("queued_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "playback_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("schedule_id", sa.String(36), sa.ForeignKey("schedules.id"), nullable=True),
        sa.Column("audio_file_id", sa.String(36), nullable=True),
        sa.Column("voice_cache_id", sa.String(36), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("delay_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("audio_device", sa.String(255), nullable=False, server_default=""),
        sa.Column("result", sa.String(16), nullable=False, server_default="success"),
        sa.Column("error_message", sa.String(1024), nullable=False, server_default=""),
    )

    op.create_table(
        "ntp_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("synced_at", sa.DateTime(), nullable=False),
        sa.Column("server", sa.String(255), nullable=False, server_default=""),
        sa.Column("offset_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("error_message", sa.String(1024), nullable=False, server_default=""),
    )

    op.create_table(
        "system_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("level", sa.String(16), nullable=False, server_default="INFO"),
        sa.Column("category", sa.String(32), nullable=False, server_default="system"),
        sa.Column("message", sa.String(2048), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("system_events")
    op.drop_table("ntp_history")
    op.drop_table("playback_history")
    op.drop_table("playback_queue")
    op.drop_table("schedule_events")
    op.drop_table("schedule_rules")
    op.drop_table("schedules")
    op.drop_index("ix_voice_cache_cache_key", table_name="voice_cache")
    op.drop_table("voice_cache")
    op.drop_table("voice_variables")
    op.drop_table("voice_templates")
    op.drop_table("audio_files")
    op.drop_table("settings")
