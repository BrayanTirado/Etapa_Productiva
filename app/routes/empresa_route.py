from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.users import Empresa, Contrato
from app import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

bp = Blueprint('empresa_bp', __name__, url_prefix='/empresa')

# --- LISTAR ---
@bp.route('/')
def listar_empresas():
    empresas = Empresa.query.all()
    return render_template('empresa/listar_empresa.html', empresas=empresas)

# --- CREAR ---
@bp.route('/nueva', methods=['GET', 'POST'])
def nueva_empresa():
    # Evitar registro adicional si ya hay empresa
    if Empresa.query.first():
        flash('Ya existe una empresa registrada. Contacta al instructor para cambios.', 'warning')
        return redirect(url_for('empresa_bp.listar_empresas'))

    if request.method == 'POST':
        try:
            # Convertir fechas a objetos datetime.date
            fecha_inicio = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date()

            # Crear empresa
            nueva = Empresa(
                nombre_empresa=request.form.get('nombre_empresa'),
                nit=request.form.get('nit'),
                direccion=request.form.get('direccion'),
                telefono=request.form.get('telefono'),
                correo_empresa=request.form.get('correo_empresa')
            )
            db.session.add(nueva)
            db.session.flush()  # Obtener ID antes del commit

            # Crear contrato
            contrato = Contrato(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                tipo_contrato=request.form.get('tipo_contrato'),
                empresa_id_empresa=nueva.id_empresa
            )
            db.session.add(contrato)
            db.session.commit()

            flash('Empresa y contrato registrados con éxito ✅', 'success')
            return redirect(url_for('empresa_bp.listar_empresas'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Ocurrió un error al guardar la empresa o el contrato ❌ {e}', 'danger')

    return render_template('empresa/nueva_empresa.html')

# --- EDITAR ---
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    contrato = empresa.contratos[0] if empresa.contratos else None

    if request.method == 'POST':
        try:
            empresa.nombre_empresa = request.form.get('nombre_empresa')
            empresa.nit = request.form.get('nit')
            empresa.direccion = request.form.get('direccion')
            empresa.telefono = request.form.get('telefono')
            empresa.correo_empresa = request.form.get('correo_empresa')

            if contrato:
                contrato.fecha_inicio = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date()
                contrato.fecha_fin = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date()
                contrato.tipo_contrato = request.form.get('tipo_contrato')

            db.session.commit()
            flash('Empresa y contrato actualizados correctamente ✏️', 'success')
            return redirect(url_for('empresa_bp.listar_empresas'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Ocurrió un error al actualizar la empresa o contrato ❌ {e}', 'danger')

    return render_template('empresa/editar_empresa.html', empresa=empresa, contrato=contrato)

# --- ELIMINAR ---
@bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    try:
        db.session.delete(empresa)
        db.session.commit()
        flash('Empresa eliminada con éxito 🗑️', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('Ocurrió un error al eliminar la empresa ❌', 'danger')
    return redirect(url_for('empresa_bp.listar_empresas'))
