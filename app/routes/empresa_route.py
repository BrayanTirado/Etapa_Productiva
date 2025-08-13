from flask import Blueprint, render_template, request, redirect, url_for
from app.models.users import Empresa
from app import db

bp = Blueprint('empresa_bp', __name__, url_prefix='/empresa')

@bp.route('/')
def listar_empresas():
    empresas = Empresa.query.all()
    return render_template('empresa/listar.html', empresas=empresas)

@bp.route('/nueva', methods=['GET', 'POST'])
def nueva_empresa():
    if request.method == 'POST':
        nueva = Empresa(
            nombre_empresa=request.form['nombre_empresa'],
            nit=request.form['nit'],
            sector=request.form['sector'],
            direccion=request.form['direccion'],
            telefono=request.form['telefono'],
            correo_empresa=request.form['correo_empresa'],
            nombre_tutor=request.form['nombre_tutor'],
            cargo_tutor=request.form['cargo_tutor']
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect(url_for('empresa_bp.listar_empresas'))

    return render_template('empresa/nueva.html')

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    if request.method == 'POST':
        empresa.nombre_empresa = request.form['nombre_empresa']
        empresa.nit = request.form['nit']
        empresa.sector = request.form['sector']
        empresa.direccion = request.form['direccion']
        empresa.telefono = request.form['telefono']
        empresa.correo_empresa = request.form['correo_empresa']
        empresa.nombre_tutor = request.form['nombre_tutor']
        empresa.cargo_tutor = request.form['cargo_tutor']
        db.session.commit()
        return redirect(url_for('empresa_bp.listar_empresas'))
    return render_template('empresa/editar.html', empresa=empresa)

@bp.route('/eliminar/<int:id>')
def eliminar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    db.session.delete(empresa)
    db.session.commit()
    return redirect(url_for('empresa_bp.listar_empresas'))
