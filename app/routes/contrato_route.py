from flask import Blueprint, render_template, request, redirect, url_for
from app.models.users import Contrato, Aprendiz
from app import db
from datetime import datetime

bp = Blueprint('contrato_bp', __name__, url_prefix='/contrato')


# --- LISTAR ---
@bp.route('/')
def listar_contratos():
    contratos = Contrato.query.all()
    return render_template('contrato/listar.html', contratos=contratos, now=datetime.now())


# --- NUEVO ---
@bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_contrato():
    if request.method == 'POST':
        nuevo = Contrato(
            fecha_inicio=request.form['fecha_inicio'],
            fecha_fin=request.form['fecha_fin'],
            tipo_contrato=request.form['tipo_contrato'],
            empresa_id_empresa=request.form['empresa_id_empresa']  # nombre correcto
        )
        db.session.add(nuevo)
        db.session.commit()

        # 🔗 Asignar contrato al aprendiz
        aprendiz_id = request.form.get('aprendiz_id')  # debe venir del formulario
        if aprendiz_id:
            aprendiz = Aprendiz.query.get(int(aprendiz_id))
            if aprendiz:
                aprendiz.contrato_id = nuevo.id_contrato
                db.session.commit()

        return redirect(url_for('contrato_bp.listar_contratos'))

    # Pasar lista de aprendices al formulario
    aprendices = Aprendiz.query.all()
    return render_template('contrato/nuevo.html', aprendices=aprendices)


# --- EDITAR ---
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_contrato(id):
    contrato = Contrato.query.get_or_404(id)
    if request.method == 'POST':
        contrato.fecha_inicio = request.form['fecha_inicio']
        contrato.fecha_fin = request.form['fecha_fin']
        contrato.tipo_contrato = request.form['tipo_contrato']
        contrato.empresa_id_empresa = request.form['empresa_id_empresa']
        db.session.commit()

        # 🔗 Actualizar aprendiz asignado (opcional)
        aprendiz_id = request.form.get('aprendiz_id')
        if aprendiz_id:
            aprendiz = Aprendiz.query.get(int(aprendiz_id))
            if aprendiz:
                aprendiz.contrato_id = contrato.id_contrato
                db.session.commit()

        return redirect(url_for('contrato_bp.listar_contratos'))

    aprendices = Aprendiz.query.all()
    return render_template('contrato/editar.html', contrato=contrato, aprendices=aprendices)


# --- ELIMINAR ---
@bp.route('/eliminar/<int:id>')
def eliminar_contrato(id):
    contrato = Contrato.query.get_or_404(id)
    db.session.delete(contrato)
    db.session.commit()
    return redirect(url_for('contrato_bp.listar_contratos'))
