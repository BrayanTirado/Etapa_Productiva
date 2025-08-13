from flask import Blueprint, render_template, request, redirect, url_for
from app.models.users import Aprendiz
from app import db

bp = Blueprint('aprendiz_bp', __name__, url_prefix='/aprendiz')

@bp.route('/')
def listar_aprendices():
    aprendices = Aprendiz.query.all()
    return render_template('aprendiz/listar.html', aprendices=aprendices)

@bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_aprendiz():
    if request.method == 'POST':
        nuevo = Aprendiz(
            nombre=request.form['nombre'],
            apellido=request.form['apellido'],
            tipo_documento=request.form['tipo_documento'],
            documento=request.form['documento'],
            email=request.form['email'],
            celular=request.form['celular'],
            ficha=request.form['ficha'],
            Contrato_idContrato=request.form['Contrato_idContrato']
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('aprendiz_bp.listar_aprendices'))
    return render_template('aprendiz/nuevo.html')

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_aprendiz(id):
    aprendiz = Aprendiz.query.get_or_404(id)
    if request.method == 'POST':
        aprendiz.nombre = request.form['nombre']
        aprendiz.apellido = request.form['apellido']
        aprendiz.tipo_documento = request.form['tipo_documento']
        aprendiz.documento = request.form['documento']
        aprendiz.email = request.form['email']
        aprendiz.celular = request.form['celular']
        aprendiz.ficha = request.form['ficha']
        aprendiz.Contrato_idContrato = request.form['Contrato_idContrato']
        db.session.commit()
        return redirect(url_for('aprendiz_bp.listar_aprendices'))
    return render_template('aprendiz/editar.html', aprendiz=aprendiz)

@bp.route('/eliminar/<int:id>')
def eliminar_aprendiz(id):
    aprendiz = Aprendiz.query.get_or_404(id)
    db.session.delete(aprendiz)
    db.session.commit()
    return redirect(url_for('aprendiz_bp.listar_aprendices'))
