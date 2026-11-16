from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '184876279938'
down_revision: Union[str, Sequence[str], None] = 'eb828c1a9ecc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.drop_column('pages')


def downgrade() -> None:
    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pages', sa.INTEGER(), nullable=True))
