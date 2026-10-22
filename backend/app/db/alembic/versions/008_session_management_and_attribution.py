"""Session management, API key attribution and webhook failure tracking

Adds:
  - refresh_tokens: server-side record of issued refresh tokens, enabling
    rotation, revocation and reuse detection.
  - password_reset_tokens: single-use password reset tokens.
  - usage_logs.api_key_id: attributes traffic to the key that made it, so a
    revoked key's traffic is still traceable.
  - webhooks.consecutive_failures: stops a single failed delivery from
    permanently disabling a webhook.
  - webhook_events.payload becomes nullable so the body can be dropped after
    a terminal delivery.

Revision ID: 008
Revises: 007
Create Date: 2026-10-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # refresh_tokens
    # ------------------------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("family_id", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["replaced_by_id"], ["refresh_tokens.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # ------------------------------------------------------------------
    # password_reset_tokens
    # ------------------------------------------------------------------
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "token_hash", name="uq_password_reset_tokens_token_hash"
        ),
    )
    op.create_index(
        "ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"]
    )
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
    )

    # ------------------------------------------------------------------
    # usage_logs.api_key_id
    # ------------------------------------------------------------------
    op.add_column(
        "usage_logs",
        sa.Column("api_key_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "usage_logs_api_key_id_fkey",
        "usage_logs",
        "api_keys",
        ["api_key_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_usage_logs_api_key_id", "usage_logs", ["api_key_id"])

    # ------------------------------------------------------------------
    # webhooks.consecutive_failures
    # ------------------------------------------------------------------
    op.add_column(
        "webhooks",
        sa.Column(
            "consecutive_failures",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # ------------------------------------------------------------------
    # webhook_events.payload becomes nullable
    # ------------------------------------------------------------------
    op.alter_column(
        "webhook_events",
        "payload",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "webhook_events",
        "payload",
        existing_type=sa.Text(),
        nullable=False,
    )

    op.drop_column("webhooks", "consecutive_failures")

    op.drop_index("ix_usage_logs_api_key_id", table_name="usage_logs")
    op.drop_constraint("usage_logs_api_key_id_fkey", "usage_logs", type="foreignkey")
    op.drop_column("usage_logs", "api_key_id")

    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
