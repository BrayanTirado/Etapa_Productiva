from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.users import Empresa
from app import db
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('empresa_bp', __name__, url_prefix='/empresa')

# --- LISTAR ---
@bp.route('/')
def listar_empresas():
    empresas = Empresa.query.all()
    return render_template('empresa/listar_empresa.html', empresas=empresas)

# --- CREAR ---
@bp.route('/nueva', methods=['GET', 'POST'])
def nueva_empresa():
    if request.method == 'POST':
        try:
            nueva = Empresa(
                nombre_empresa=request.form.get('nombre_empresa'),
                nit=request.form.get('nit'),
                sector=request.form.get('sector'),
                direccion=request.form.get('direccion'),
                telefono=request.form.get('telefono'),
                correo_empresa=request.form.get('correo_empresa'),
                nombre_tutor=request.form.get('nombre_tutor'),
                cargo_tutor=request.form.get('cargo_tutor')
            )
            db.session.add(nueva)
            db.session.commit()
            flash('Empresa registrada con éxito ✅', 'success')
            return redirect(url_for('empresa_bp.listar_empresas'))
        except SQLAlchemyError:
            db.session.rollback()
            flash('Ocurrió un error al guardar la empresa ❌', 'danger')

    return render_template('empresa/nueva_empresa.html')

# --- EDITAR ---
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    if request.method == 'POST':
        try:
            empresa.nombre_empresa = request.form.get('nombre_empresa')
            empresa.nit = request.form.get('nit')
            empresa.sector = request.form.get('sector')
            empresa.direccion = request.form.get('direccion')
            empresa.telefono = request.form.get('telefono')
            empresa.correo_empresa = request.form.get('correo_empresa')
            empresa.nombre_tutor = request.form.get('nombre_tutor')
            empresa.cargo_tutor = request.form.get('cargo_tutor')

            db.session.commit()
            flash('Empresa actualizada correctamente ✏️', 'success')
            return redirect(url_for('empresa_bp.listar_empresas'))
        except SQLAlchemyError:
            db.session.rollback()
            flash('Ocurrió un error al actualizar la empresa ❌', 'danger')

    return render_template('empresa/editar_empresa.html', empresa=empresa)

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
