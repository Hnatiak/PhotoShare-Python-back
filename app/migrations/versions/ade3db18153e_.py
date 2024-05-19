"""empty message

Revision ID: ade3db18153e
Revises: 0eea573817d0, 3019bc5f8124
Create Date: 2024-05-19 19:49:29.329173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ade3db18153e'
down_revision: Union[str, None] = ('0eea573817d0', '3019bc5f8124')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
