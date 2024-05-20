"""empty message

Revision ID: 1d06e3b23af5
Revises: ade3db18153e
Create Date: 2024-05-20 14:07:27.736928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d06e3b23af5'
down_revision: Union[str, None] = 'ade3db18153e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
