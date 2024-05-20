"""empty message

Revision ID: 3a6c921c0136
Revises: 64da0241a576
Create Date: 2024-05-20 13:59:52.307766

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a6c921c0136'
down_revision: Union[str, None] = '64da0241a576'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
