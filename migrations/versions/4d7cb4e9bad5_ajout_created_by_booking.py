"""ajout created_by Booking

Revision ID: 4d7cb4e9bad5
Revises: 06a46dbc5020
Create Date: 2025-08-21 15:54:00.955955

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d7cb4e9bad5'
down_revision = '06a46dbc5020'
branch_labels = None
depends_on = None


def upgrade():
    # Ajoutez la colonne avec une valeur par défaut
    op.add_column('booking', sa.Column('created_by', sa.String(length=50), nullable=True))
    # Supprimez les colonnes inutiles
    op.drop_column('booking', 'date_updated')
    op.drop_column('booking', 'updated_by')

def downgrade():
    # Recréez les colonnes supprimées
    op.add_column('booking', sa.Column('updated_by', sa.INTEGER(), nullable=True))
    op.add_column('booking', sa.Column('date_updated', sa.DATETIME(), nullable=True))
    # Supprimez la colonne created_by
    op.drop_column('booking', 'created_by')
