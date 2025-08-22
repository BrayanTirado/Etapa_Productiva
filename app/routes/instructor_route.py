# Rutas CRUD de Instructor (Create, Update, Delete)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.users import Instructor
from app import db
from werkzeug.security import generate_password_hash
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

# Blueprint para instructores
bp = Blueprint('instructor_bp', __name__, url_prefix='/instructor')

# ---- CREAR NUEVO INSTRUCTOR ----
@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_instructor():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        correo = request.form.get('correo')
        celular = request.form.get('celular')
        password = request.form.get('password')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular, password]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        hashed_password = generate_password_hash(password)
        nuevo = Instructor(
            nombre_instructor=nombre,
            apellido_instructor=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            correo_instructor=correo,
            celular_instructor=celular,
            passwordInstructor=hashed_password
        )

        try:
            db.session.add(nuevo)
            db.session.commit()
            flash('Instructor creado exitosamente.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un instructor con ese documento, correo o celular.', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el instructor: {str(e)}', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

    return render_template('instructor.html')

# ---- EDITAR INSTRUCTOR ----
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_instructor(id):
    instructor = Instructor.query.get_or_404(id)

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        correo = request.form.get('correo')
        celular = request.form.get('celular')
        password = request.form.get('password')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('instructor_bp.editar_instructor', id=id))

        instructor.nombre_instructor = nombre
        instructor.apellido_instructor = apellido
        instructor.tipo_documento = tipo_documento
        instructor.documento = documento
        instructor.correo_instructor = correo
        instructor.celular_instructor = celular
        if password:
            instructor.passwordInstructor = generate_password_hash(password)

        try:
            db.session.commit()
            flash('Instructor actualizado correctamente.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Documento, correo o celular duplicado.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('instructor.html', instructor=instructor, mode='edit')

# ---- ELIMINAR INSTRUCTOR ----
@bp.route('/eliminar/<int:id>')
@login_required
def eliminar_instructor(id):
    instructor = Instructor.query.get_or_404(id)
    try:    
        db.session.delete(instructor)
        db.session.commit()
        flash('Instructor eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar instructor: {str(e)}', 'danger')
    return redirect(url_for('auth.login'))

# ---- PERFIL DEL INSTRUCTOR ----
@bp.route('/perfil')
@login_required
def perfil_instructor():
    # Aseguramos que solo los instructores puedan entrar aquí
    if not hasattr(current_user, "id_instructor"):
        flash("No tienes permiso para acceder a este perfil.", "danger")
        return redirect(url_for("perfil_instructor"))  # o a donde quieras redirigir

    return render_template("perfil_instructor.html", instructor=current_user)
