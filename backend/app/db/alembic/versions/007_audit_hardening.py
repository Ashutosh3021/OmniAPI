"""Audit hardening: usage log SET NULL, webhook secrets, service uniqueness

Revision ID: 007
Revises: 006
Create Date: 2026-05-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "usage_logs_service_id_fkey", "usage_logs", type_="foreignkey"
    )
    op.alter_column("usage_logs", "service_id", existing_type=sa.Integer(), nullable=True)
    op.create_foreign_key(
        "usage_logs_service_id_fkey",
        "usage_logs",
        "external_services",
        ["service_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "webhooks",
        sa.Column("secret_encrypted", sa.String(length=500), nullable=True),
    )

    op.create_unique_constraint(
        "uq_external_services_user_id_service_name",
        "external_services",
        ["user_id", "service_name"],
    )

    op.create_index(
        "ix_api_keys_key_hash",
        "api_keys",
        ["key_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_api_keys_key_hash", table_name="api_keys")
    op.drop_constraint(
        "uq_external_services_user_id_service_name", "external_services", type_="unique"
    )
    op.drop_column("webhooks", "secret_encrypted")

    op.drop_constraint(
        "usage_logs_service_id_fkey", "usage_logs", type_="foreignkey"
    )
    op.alter_column("usage_logs", "service_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key(
        "usage_logs_service_id_fkey",
        "usage_logs",
        "external_services",
        ["service_id"],
        ["id"],
        ondelete="CASCADE",
    )
