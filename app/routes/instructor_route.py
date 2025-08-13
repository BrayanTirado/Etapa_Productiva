from flask import Blueprint, render_template, request, redirect, url_for
from app.models.users import Instructor
from app import db

bp = Blueprint('instructor_bp', __name__, url_prefix='/instructor')

@bp.route('/')
def listar_instructores():
    instructores = Instructor.query.all()
    return render_template('instructor/listar.html', instructores=instructores)

@bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_instructor():
    if request.method == 'POST':
        nuevo = Instructor(
            nombre_instructor=request.form['nombre_instructor'],
            apellido_instructor=request.form['apellido_instructor'],
            correo_instructor=request.form['correo_instructor'],
            celular_instructor=request.form['celular_instructor'],
            tipo_documento=request.form['tipo_documento'],
            documento=request.form['documento'],
            rol=request.form['rol']
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('instructor_bp.listar_instructores'))
    return render_template('instructor/nuevo.html')

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_instructor(id):
    instructor = Instructor.query.get_or_404(id)
    if request.method == 'POST':
        instructor.nombre_instructor = request.form['nombre_instructor']
        instructor.apellido_instructor = request.form['apellido_instructor']
        instructor.correo_instructor = request.form['correo_instructor']
        instructor.celular_instructor = request.form['celular_instructor']
        instructor.tipo_documento = request.form['tipo_documento']
        instructor.documento = request.form['documento']
        instructor.rol = request.form['rol']
        db.session.commit()
        return redirect(url_for('instructor_bp.listar_instructores'))
    return render_template('instructor/editar.html', instructor=instructor)

@bp.route('/eliminar/<int:id>')
def eliminar_instructor(id):
    instructor = Instructor.query.get_or_404(id)
    db.session.delete(instructor)
    db.session.commit()
    return redirect(url_for('instructor_bp.listar_instructores'))
