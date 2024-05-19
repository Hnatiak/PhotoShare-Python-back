"""empty message

Revision ID: 141158139bab
Revises: c4471cb7cc11
Create Date: 2024-05-18 21:22:16.821165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '141158139bab'
down_revision: Union[str, None] = 'c4471cb7cc11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
