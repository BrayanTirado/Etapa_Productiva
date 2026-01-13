"""Migracion inicial v2.0

Revision ID: 65c8383be3b7
Revises:
Create Date: 2026-01-13 09:49:48.318048
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '65c8383be3b7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # =====================================================
    # ELIMINAR TABLAS DEPENDIENTES DEL COORDINADOR
    # =====================================================
    op.drop_table('token_coordinador')
    op.drop_table('admin_sede')

    # =====================================================
    # APRENDIZ
    # =====================================================
    with op.batch_alter_table('aprendiz', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('aprendiz_coordinador_id_fkey'), type_='foreignkey')
        batch_op.drop_column('coordinador_id')
        batch_op.add_column(sa.Column('correo', sa.String(length=100), nullable=False))
        batch_op.add_column(
            sa.Column(
                'jornada',
                sa.Enum('Mañana', 'Tarde', 'Noche', name='jornada_aprendiz_enum'),
                nullable=False
            )
        )
        batch_op.drop_index(batch_op.f('ix_aprendiz_email'))
        batch_op.create_index(batch_op.f('ix_aprendiz_correo'), ['correo'], unique=True)
        batch_op.drop_column('email')

    # =====================================================
    # INSTRUCTOR
    # =====================================================
    with op.batch_alter_table('instructor', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('instructor_coordinador_id_fkey'), type_='foreignkey')
        batch_op.drop_column('coordinador_id')
        batch_op.add_column(sa.Column('administrador_sede_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(
            None,
            'administrador_sede',
            ['administrador_sede_id'],
            ['id_admin_sede']
        )

    # =====================================================
    # TOKEN INSTRUCTOR
    # =====================================================
    with op.batch_alter_table('token_instructor', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('token_instructor_coordinador_id_fkey'), type_='foreignkey')
        batch_op.drop_column('coordinador_id')

    # =====================================================
    # PROGRAMA
    # =====================================================
    with op.batch_alter_table('programa', schema=None) as batch_op:
        batch_op.drop_column('jornada')

    # =====================================================
    # SEDE
    # =====================================================
    with op.batch_alter_table('sede', schema=None) as batch_op:
        batch_op.alter_column(
            'nombre_sede',
            existing_type=postgresql.ENUM(
                'CGAO', 'CCS', 'CDM', 'CGAF', 'CGPI',
                'CTIC', 'CBA', 'CEM', 'CSF', 'CFGR',
                name='nombre_sede_enum'
            ),
            type_=sa.String(length=50),
            existing_nullable=False
        )

    # =====================================================
    # FINALMENTE ELIMINAR COORDINADOR
    # =====================================================
    op.drop_table('coordinador')


def downgrade():
    pass
