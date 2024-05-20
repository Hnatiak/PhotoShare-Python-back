"""empty message

Revision ID: 660ec0712591
Revises: 3a6c921c0136, 7dda20673fa9
Create Date: 2024-05-20 14:32:13.389377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '660ec0712591'
down_revision: Union[str, None] = ('3a6c921c0136', '7dda20673fa9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
