"""Change col name

Revision ID: 46cfe729d1ae
Revises: 2f1377edc7fa
Create Date: 2022-07-17 19:47:46.879172

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "46cfe729d1ae"
down_revision = "2f1377edc7fa"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("conversion_job", sa.Column("message", sa.Text(), nullable=True))
    op.add_column(
        "conversion_job", sa.Column("status", sa.String(length=16), nullable=True)
    )
    op.drop_column("conversion_job", "latest_message")
    op.drop_column("conversion_job", "latest_status")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "conversion_job",
        sa.Column(
            "latest_status", sa.VARCHAR(length=16), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "conversion_job",
        sa.Column("latest_message", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.drop_column("conversion_job", "status")
    op.drop_column("conversion_job", "message")
    # ### end Alembic commands ###
