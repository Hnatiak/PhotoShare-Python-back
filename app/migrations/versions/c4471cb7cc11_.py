"""empty message

Revision ID: c4471cb7cc11
Revises: 251abd473797, d9217439cbb2
Create Date: 2024-05-18 19:37:50.613247

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4471cb7cc11'
down_revision: Union[str, None] = ('251abd473797', 'd9217439cbb2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
