from flask import Blueprint, render_template, request, redirect, url_for
from app.models.users import Evidencia
from app import db

bp = Blueprint('evidencia_bp', __name__, url_prefix='/evidencia')

@bp.route('/')
def listar_evidencias():
    evidencias = Evidencia.query.all()
    return render_template('evidencia/listar.html', evidencias=evidencias)

@bp.route('/nueva', methods=['GET', 'POST'])
def nueva_evidencia():
    if request.method == 'POST':
        nueva = Evidencia(
            formato=request.form['formato'],
            nombre_archivo=request.form['nombre_archivo'],
            url_archivo=request.form['url_archivo'],
            fecha_subida=request.form['fecha_subida'],
            Aprendiz_idAprendiz=request.form['Aprendiz_idAprendiz'],
            tipo=request.form['tipo']
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect(url_for('evidencia_bp.listar_evidencias'))
    return render_template('evidencia/nueva.html')

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_evidencia(id):
    evidencia = Evidencia.query.get_or_404(id)
    if request.method == 'POST':
        evidencia.formato = request.form['formato']
        evidencia.nombre_archivo = request.form['nombre_archivo']
        evidencia.url_archivo = request.form['url_archivo']
        evidencia.fecha_subida = request.form['fecha_subida']
        evidencia.Aprendiz_idAprendiz = request.form['Aprendiz_idAprendiz']
        evidencia.tipo = request.form['tipo']
        db.session.commit()
        return redirect(url_for('evidencia_bp.listar_evidencias'))
    return render_template('evidencia/editar.html', evidencia=evidencia)

@bp.route('/eliminar/<int:id>')
def eliminar_evidencia(id):
    evidencia = Evidencia.query.get_or_404(id)
    db.session.delete(evidencia)
    db.session.commit()
    return redirect(url_for('evidencia_bp.listar_evidencias'))
