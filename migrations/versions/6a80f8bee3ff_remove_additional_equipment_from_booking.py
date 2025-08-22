from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6a80f8bee3ff'
down_revision = '4d7cb4e9bad5'
branch_labels = None
depends_on = None

def upgrade():
    # Remove the additional_equipment column
    op.drop_column('booking', 'additional_equipment')

def downgrade():
    # Re-add the additional_equipment column if rolling back
    pass