from flask import Blueprint, render_template, request, redirect, url_for
from app.models.users import Programa
from app import db

bp = Blueprint('programa_bp', __name__, url_prefix='/programa')

@bp.route('/')
def listar_programas():
    programas = Programa.query.all()
    return render_template('programa/listar_programa.html', programas=programas)

@bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_programa():
    if request.method == 'POST':
        nuevo = Programa(
            nombre_programa=request.form['nombre_programa'],
            nivel=request.form['nivel'],
            jornada=request.form['jornada'],
            centro_formacion=request.form['centro_formacion'],
            aprendiz_id_aprendiz=request.form['aprendiz_id_aprendiz'],
            instructor_id_instructor=request.form['instructor_id_instructor']
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('programa_bp.listar_programas'))
    return render_template('programa/nuevo_programa.html')

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_programa(id):
    programa = Programa.query.get_or_404(id)
    if request.method == 'POST':
        programa.nombre_programa = request.form['nombre_programa']
        programa.nivel = request.form['nivel']
        programa.jornada = request.form['jornada']
        programa.centro_formacion = request.form['centro_formacion']
        programa.aprendiz_id_aprendiz = request.form['aprendiz_id_aprendiz']
        programa.instructor_id_instructor = request.form['instructor_id_instructor']
        db.session.commit()
        return redirect(url_for('programa_bp.listar_programas'))
    return render_template('programa/editar_programa.html', programa=programa)

@bp.route('/eliminar/<int:id>')
def eliminar_programa(id):
    programa = Programa.query.get_or_404(id)
    db.session.delete(programa)
    db.session.commit()
    return redirect(url_for('programa_bp.listar_programas'))
