# Rutas CRUD de Aprendiz (Create, Update, Delete y Perfil)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.users import Aprendiz
from app import db
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

# Blueprint para aprendices
bp = Blueprint('aprendiz_bp', __name__, url_prefix='/aprendiz')


# ---- CREAR NUEVO APRENDIZ ----
@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_aprendiz():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        email = request.form.get('email')
        celular = request.form.get('celular')
        ficha = request.form.get('ficha')
        contrato_id_contrato = request.form.get('contrato_id_contrato')
        password_aprendiz = request.form.get('password_aprendiz')

        # Validar que los campos estén completos
        if not all([nombre, apellido, tipo_documento, documento, email, celular, ficha, contrato_id_contrato, password_aprendiz]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('aprendiz_bp.nuevo_aprendiz'))

        try:
            ficha = int(ficha)
            contrato_id_contrato = int(contrato_id_contrato)
        except ValueError:
            flash('Ficha y contrato deben ser números válidos.', 'danger')
            return redirect(url_for('aprendiz_bp.nuevo_aprendiz'))

        hashed_password = generate_password_hash(password_aprendiz)

        nuevo = Aprendiz(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            email=email,
            celular=celular,
            ficha=ficha,
            contrato_id_contrato=contrato_id_contrato,
            password_aprendiz=hashed_password
        )

        try:
            db.session.add(nuevo)
            db.session.commit()
            flash('Aprendiz creado exitosamente.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un aprendiz con ese documento, correo o celular.', 'danger')
            return redirect(url_for('aprendiz_bp.nuevo_aprendiz'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el aprendiz: {str(e)}', 'danger')
            return redirect(url_for('aprendiz_bp.nuevo_aprendiz'))

    return render_template('aprendiz/nuevo.html')  # Asegúrate de tener este template


# ---- EDITAR APRENDIZ ----
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_aprendiz(id):
    aprendiz = Aprendiz.query.get_or_404(id)

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        email = request.form.get('email')
        celular = request.form.get('celular')
        ficha = request.form.get('ficha')
        contrato_id_contrato = request.form.get('contrato_id_contrato')
        password_aprendiz = request.form.get('password_aprendiz')

        if not all([nombre, apellido, tipo_documento, documento, email, celular, ficha, contrato_id_contrato]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

        try:
            ficha = int(ficha)
            contrato_id_contrato = int(contrato_id_contrato)
        except ValueError:
            flash('Ficha y contrato deben ser numéricos.', 'danger')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

        # Actualizar datos
        aprendiz.nombre = nombre
        aprendiz.apellido = apellido
        aprendiz.tipo_documento = tipo_documento
        aprendiz.documento = documento
        aprendiz.email = email
        aprendiz.celular = celular
        aprendiz.ficha = ficha
        aprendiz.contrato_id_contrato = contrato_id_contrato
        if password_aprendiz:
            aprendiz.password_aprendiz = generate_password_hash(password_aprendiz)

        try:
            db.session.commit()
            flash('Aprendiz actualizado correctamente.', 'success')
            # Redirige a la lista de estudiantes o al perfil del aprendiz según tu flujo
            return redirect(url_for('estudiantes_bp.listar_estudiantes'))
        except IntegrityError:
            db.session.rollback()
            flash('Documento, email o celular duplicado.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    # Reutilizamos el perfil para la edición
    return render_template('perfil_aprendiz.html', aprendiz=aprendiz, mode='edit')


# ---- ELIMINAR APRENDIZ ----
@bp.route('/eliminar/<int:id>')
@login_required
def eliminar_aprendiz(id):
    aprendiz = Aprendiz.query.get_or_404(id)
    try:
        db.session.delete(aprendiz)
        db.session.commit()
        flash('Aprendiz eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('estudiantes_bp.listar_estudiantes'))


# ---- PERFIL DEL APRENDIZ ----
@bp.route('/perfil')
@login_required
def perfil_aprendiz():
    if not hasattr(current_user, "id_aprendiz"):
        flash("No tienes permiso para acceder a este perfil.", "danger")
        return redirect(url_for("auth.dashboard"))  # Redirigir a un dashboard seguro
    return render_template("perfil_aprendiz.html", aprendiz=current_user)
