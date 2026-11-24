"""One-time tokens for leave request forms.

Revision ID: 0003_submission
Revises: 0002_decision
Create Date: 2026-11-24

"""

from alembic import op
import sqlalchemy as sa

revision = "0003_submission"
down_revision = "0002_decision"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "submission_tokens",
        sa.Column("token", sa.String(length=64), primary_key=True),
        sa.Column("leave_request_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["leave_request_id"], ["leave_requests.id"]),
    )


def downgrade() -> None:
    op.drop_table("submission_tokens")
