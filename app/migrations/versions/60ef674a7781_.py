"""empty message

Revision ID: 60ef674a7781
Revises: 1d06e3b23af5
Create Date: 2024-05-20 14:13:44.256578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60ef674a7781'
down_revision: Union[str, None] = '1d06e3b23af5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
