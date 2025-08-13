from flask import Blueprint, render_template, request, redirect, url_for
from app.models.users import Contrato
from app import db

bp = Blueprint('contrato_bp', __name__, url_prefix='/contrato')

@bp.route('/')
def listar_contratos():
    contratos = Contrato.query.all()
    return render_template('contrato/listar.html', contratos=contratos)

@bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_contrato():
    if request.method == 'POST':
        nuevo = Contrato(
            fecha_inicio=request.form['fecha_inicio'],
            fecha_fin=request.form['fecha_fin'],
            tipo_contrato=request.form['tipo_contrato'],
            Empresa_idEmpresa=request.form['Empresa_idEmpresa']
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('contrato_bp.listar_contratos'))
    return render_template('contrato/nuevo.html')

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_contrato(id):
    contrato = Contrato.query.get_or_404(id)
    if request.method == 'POST':
        contrato.fecha_inicio = request.form['fecha_inicio']
        contrato.fecha_fin = request.form['fecha_fin']
        contrato.tipo_contrato = request.form['tipo_contrato']
        contrato.Empresa_idEmpresa = request.form['Empresa_idEmpresa']
        db.session.commit()
        return redirect(url_for('contrato_bp.listar_contratos'))
    return render_template('contrato/editar.html', contrato=contrato)

@bp.route('/eliminar/<int:id>')
def eliminar_contrato(id):
    contrato = Contrato.query.get_or_404(id)
    db.session.delete(contrato)
    db.session.commit()
    return redirect(url_for('contrato_bp.listar_contratos'))
