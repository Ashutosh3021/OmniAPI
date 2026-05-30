"""Create webhook_events table

Revision ID: 006
Revises: 005
Create Date: 2026-05-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

webhook_event_status = postgresql.ENUM(
    "pending",
    "delivered",
    "failed",
    name="webhook_event_status",
    create_type=False,
)


def upgrade() -> None:
    postgresql.ENUM(
        "pending", "delivered", "failed", name="webhook_event_status"
    ).create(op.get_bind(), checkfirst=True)
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("webhook_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column(
            "status",
            webhook_event_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["webhook_id"], ["webhooks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_webhook_events_id"), "webhook_events", ["id"], unique=False)
    op.create_index(
        op.f("ix_webhook_events_webhook_id"), "webhook_events", ["webhook_id"], unique=False
    )
    op.create_index(
        op.f("ix_webhook_events_user_id"), "webhook_events", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_webhook_events_created_at"), "webhook_events", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_webhook_events_created_at"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_user_id"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_webhook_id"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_id"), table_name="webhook_events")
    op.drop_table("webhook_events")
    webhook_event_status.drop(op.get_bind(), checkfirst=True)
