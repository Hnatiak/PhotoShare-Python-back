"""empty message

Revision ID: 7dda20673fa9
Revises: 60ef674a7781
Create Date: 2024-05-20 14:15:21.847289

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7dda20673fa9'
down_revision: Union[str, None] = '60ef674a7781'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
