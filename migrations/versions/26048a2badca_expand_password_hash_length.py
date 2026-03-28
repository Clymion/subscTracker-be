"""expand_password_hash_length

Revision ID: 26048a2badca
Revises: 36e602ae28aa
Create Date: 2026-03-28 06:46:29.501622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26048a2badca'
down_revision: Union[str, None] = '36e602ae28aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        'users',
        'password_hash',
        type_=sa.String(255),
        existing_nullable=False,
    )

def downgrade():
    op.alter_column(
        'users',
        'password_hash',
        type_=sa.String(128),
        existing_nullable=False,
    )
