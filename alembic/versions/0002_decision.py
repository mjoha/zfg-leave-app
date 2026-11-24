"""Decision comment and time on leave requests.

Revision ID: 0002_decision
Revises: 0001_initial
Create Date: 2026-11-24

"""

from alembic import op
import sqlalchemy as sa

revision = "0002_decision"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("leave_requests", sa.Column("decision_comment", sa.String(length=500), nullable=True))
    op.add_column("leave_requests", sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("leave_requests", "decided_at")
    op.drop_column("leave_requests", "decision_comment")
