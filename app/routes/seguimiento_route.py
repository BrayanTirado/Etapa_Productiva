from flask import Blueprint, render_template, request, redirect, url_for
from app.models.users import Seguimiento
from app import db
from datetime import datetime

bp = Blueprint('seguimiento_bp', __name__, url_prefix='/seguimiento')

@bp.route('/')
def listar_seguimientos():
    seguimientos = Seguimiento.query.all()
    return render_template('seguimiento/listar.html', seguimientos=seguimientos, now=datetime.now())

@bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_seguimiento():
    if request.method == 'POST':
        nuevo = Seguimiento(
            fecha=request.form['fecha'],
            tipo=request.form['tipo'],
            observaciones=request.form['observaciones'],
            Instructor_idInstructor=request.form['Instructor_idInstructor'],
            Aprendiz_idAprendiz=request.form['Aprendiz_idAprendiz']
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('seguimiento_bp.listar_seguimientos'))
    return render_template('seguimiento/nuevo.html', now=datetime.now())

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_seguimiento(id):
    seguimiento = Seguimiento.query.get_or_404(id)
    if request.method == 'POST':
        seguimiento.fecha = request.form['fecha']
        seguimiento.tipo = request.form['tipo']
        seguimiento.observaciones = request.form['observaciones']
        seguimiento.Instructor_idInstructor = request.form['Instructor_idInstructor']
        seguimiento.Aprendiz_idAprendiz = request.form['Aprendiz_idAprendiz']
        db.session.commit()
        return redirect(url_for('seguimiento_bp.listar_seguimientos'))
    return render_template('seguimiento/editar.html', seguimiento=seguimiento, now=datetime.now())

@bp.route('/eliminar/<int:id>')
def eliminar_seguimiento(id):
    seguimiento = Seguimiento.query.get_or_404(id)
    db.session.delete(seguimiento)
    db.session.commit()
    return redirect(url_for('seguimiento_bp.listar_seguimientos'))
