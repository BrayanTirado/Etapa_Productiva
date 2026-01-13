"""Migracion inicial limpia CORREGIDA

Revision ID: ad67b34e3af0
Revises: 
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa

revision = 'ad67b34e3af0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    # =========================
    # TABLAS BASE (SIN FK)
    # =========================

    op.create_table(
        'administrador',
        sa.Column('id_admin', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('apellido', sa.String(100), nullable=False),
        sa.Column('tipo_documento', sa.Enum(
            'Cedula de Ciudadania',
            'Tarjeta de Identidad',
            'Cedula Extrangeria',
            'Registro Civil',
            name='tipo_documento_enum'
        ), nullable=False),
        sa.Column('documento', sa.String(50), nullable=False, unique=True),
        sa.Column('correo', sa.String(100), nullable=False, unique=True),
        sa.Column('celular', sa.String(45), nullable=False),
        sa.Column('password', sa.String(200), nullable=False),
    )

    op.create_table(
        'sede',
        sa.Column('id_sede', sa.Integer(), primary_key=True),
        sa.Column('nombre_sede', sa.String(50), nullable=False, unique=True),
        sa.Column('ciudad', sa.String(100), nullable=False),
        sa.Column('token', sa.String(100)),
        sa.Column('token_expiracion', sa.DateTime()),
    )

    op.create_table(
        'ficha',
        sa.Column('id_ficha', sa.Integer(), primary_key=True),
        sa.Column('numero_ficha', sa.Integer(), nullable=False, unique=True)
    )

    # =========================
    # ADMINISTRADOR SEDE
    # =========================

    op.create_table(
        'administrador_sede',
        sa.Column('id_admin_sede', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('apellido', sa.String(100), nullable=False),
        sa.Column('tipo_documento', sa.Enum(
            'Cedula de Ciudadania',
            'Tarjeta de Identidad',
            'Cedula Extrangeria',
            'Registro Civil',
            name='tipo_documento_enum'
        ), nullable=False),
        sa.Column('documento', sa.String(50), nullable=False, unique=True),
        sa.Column('correo', sa.String(100), nullable=False, unique=True),
        sa.Column('celular', sa.String(45), nullable=False),
        sa.Column('password', sa.String(200), nullable=False),
        sa.Column('admin_principal_id', sa.Integer(), sa.ForeignKey('administrador.id_admin'), nullable=False),
        sa.Column('sede_id', sa.Integer(), sa.ForeignKey('sede.id_sede'), nullable=False),
    )

    # =========================
    # INSTRUCTOR
    # =========================

    op.create_table(
        'instructor',
        sa.Column('id_instructor', sa.Integer(), primary_key=True),
        sa.Column('nombre_instructor', sa.String(45), nullable=False),
        sa.Column('apellido_instructor', sa.String(45), nullable=False),
        sa.Column('correo_instructor', sa.String(100), nullable=False, unique=True),
        sa.Column('celular_instructor', sa.String(45), nullable=False),
        sa.Column('tipo_documento', sa.Enum(
            'Cedula de Ciudadania',
            'Cedula Extrangeria',
            name='tipo_documento_instructor_enum'
        ), nullable=False),
        sa.Column('documento', sa.String(45), nullable=False, unique=True),
        sa.Column('password_instructor', sa.String(250), nullable=False),
        sa.Column('administrador_sede_id', sa.Integer(), sa.ForeignKey('administrador_sede.id_admin_sede'), nullable=False),
        sa.Column('sede_id', sa.Integer(), sa.ForeignKey('sede.id_sede')),
    )

    # =========================
    # PROGRAMA
    # =========================

    op.create_table(
        'programa',
        sa.Column('id_programa', sa.Integer(), primary_key=True),
        sa.Column('nombre_programa', sa.String(45), nullable=False),
        sa.Column('titulo', sa.Enum('Auxiliar', 'Tecnico', 'Tecnologo', name='titulo_programa_enum'), nullable=False),
        sa.Column('ficha_id', sa.Integer(), sa.ForeignKey('ficha.id_ficha'), nullable=False),
        sa.Column('instructor_id_instructor', sa.Integer(), sa.ForeignKey('instructor.id_instructor')),
    )

    # =========================
    # EMPRESA (SIN CICLO)
    # =========================

    op.create_table(
        'empresa',
        sa.Column('id_empresa', sa.Integer(), primary_key=True),
        sa.Column('nombre_empresa', sa.String(100), nullable=False),
        sa.Column('nit', sa.String(45), nullable=False, unique=True),
        sa.Column('direccion', sa.String(200), nullable=False),
        sa.Column('telefono', sa.String(20), nullable=False),
        sa.Column('correo_empresa', sa.String(100), nullable=False),
        sa.Column('nombre_jefe', sa.String(150), nullable=False, unique=True),
        sa.Column('correo_jefe', sa.String(150), nullable=False, unique=True),
        sa.Column('telefono_jefe', sa.String(50), nullable=False, unique=True),
    )

    # =========================
    # CONTRATO
    # =========================

    op.create_table(
        'contrato',
        sa.Column('id_contrato', sa.Integer(), primary_key=True),
        sa.Column('fecha_inicio', sa.Date(), nullable=False),
        sa.Column('fecha_fin', sa.Date(), nullable=False),
        sa.Column('tipo_contrato', sa.Enum(
            'Contrato de Aprendizaje',
            'Contrato laboral',
            name='tipo_contrato_enum'
        ), nullable=False),
        sa.Column('empresa_id_empresa', sa.Integer(), sa.ForeignKey('empresa.id_empresa'), nullable=False),
    )

    # =========================
    # APRENDIZ (AL FINAL)
    # =========================

    op.create_table(
        'aprendiz',
        sa.Column('id_aprendiz', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(45), nullable=False),
        sa.Column('apellido', sa.String(45), nullable=False),
        sa.Column('tipo_documento', sa.Enum(
            'Cedula de Ciudadania',
            'Tarjeta de Identidad',
            'Cedula Extrangeria',
            'Registro Civil',
            name='tipo_documento_enum'
        ), nullable=False),
        sa.Column('documento', sa.String(45), nullable=False, unique=True),
        sa.Column('correo', sa.String(100), nullable=False, unique=True),
        sa.Column('celular', sa.String(45), nullable=False, unique=True),
        sa.Column('jornada', sa.Enum('Mañana', 'Tarde', 'Noche', name='jornada_aprendiz_enum'), nullable=False),
        sa.Column('password_aprendiz', sa.String(250), nullable=False),
        sa.Column('contrato_id', sa.Integer(), sa.ForeignKey('contrato.id_contrato')),
        sa.Column('programa_id', sa.Integer(), sa.ForeignKey('programa.id_programa')),
        sa.Column('instructor_id', sa.Integer(), sa.ForeignKey('instructor.id_instructor')),
        sa.Column('sede_id', sa.Integer(), sa.ForeignKey('sede.id_sede')),
    )


def downgrade():
    op.drop_table('aprendiz')
    op.drop_table('contrato')
    op.drop_table('empresa')
    op.drop_table('programa')
    op.drop_table('instructor')
    op.drop_table('administrador_sede')
    op.drop_table('ficha')
    op.drop_table('sede')
    op.drop_table('administrador')
