"""Create external_services table

Revision ID: 003
Revises: 002
Create Date: 2026-05-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

external_service_status = postgresql.ENUM(
    "active",
    "inactive",
    "error",
    name="external_service_status",
    create_type=False,
)


def upgrade() -> None:
    postgresql.ENUM(
        "active", "inactive", "error", name="external_service_status"
    ).create(op.get_bind(), checkfirst=True)
    op.create_table(
        "external_services",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("api_key_encrypted", sa.String(length=500), nullable=False),
        sa.Column("max_calls_per_hour", sa.Integer(), nullable=False, server_default="100"),
        sa.Column(
            "status",
            external_service_status,
            nullable=False,
            server_default="active",
        ),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_external_services_id"), "external_services", ["id"], unique=False)
    op.create_index(
        op.f("ix_external_services_user_id"), "external_services", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_external_services_created_at"),
        "external_services",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_external_services_user_id_created_at",
        "external_services",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_external_services_user_id_created_at", table_name="external_services")
    op.drop_index(op.f("ix_external_services_created_at"), table_name="external_services")
    op.drop_index(op.f("ix_external_services_user_id"), table_name="external_services")
    op.drop_index(op.f("ix_external_services_id"), table_name="external_services")
    op.drop_table("external_services")
    external_service_status.drop(op.get_bind(), checkfirst=True)
