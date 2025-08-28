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
        password_aprendiz = request.form.get('password_aprendiz')

        if not all([nombre, apellido, tipo_documento, documento, email, celular, ficha, password_aprendiz]):
            flash('Todos los campos son obligatorios.', 'warning')
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

    return render_template('aprendiz/nuevo.html')  

# ---- EDITAR APRENDIZ ----
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_aprendiz(id):
    aprendiz = Aprendiz.query.get_or_404(id)

    # Opciones válidas (tienen que coincidir EXACTO con lo que tienes en tu modelo Enum)
    tipos_documento = [
        'Cedula de Ciudadania',
        'Tarjeta de Identidad',
        'Cedula Extrangeria',
        'Registro Civil'
    ]
    fichas = ['2931558', '2674567', '5434234']

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento', '').strip()
        email = request.form.get('email', '').strip()
        celular = request.form.get('celular', '').strip()
        ficha = request.form.get('ficha')
        password_aprendiz = request.form.get('password_aprendiz', '').strip()

        # Validación de campos obligatorios
        if not all([nombre, apellido, tipo_documento, documento, email, celular, ficha]):
            flash('⚠️ Faltan campos obligatorios.', 'warning')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

        # Validar que los valores estén dentro de los permitidos
        if tipo_documento not in tipos_documento or ficha not in fichas:  # Corregido
            flash('❌ Valor de tipo de documento o ficha inválido.', 'danger')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

        # Actualizar datos en el objeto
        aprendiz.nombre = nombre
        aprendiz.apellido = apellido
        aprendiz.tipo_documento = tipo_documento
        aprendiz.documento = documento
        aprendiz.email = email
        aprendiz.celular = celular
        aprendiz.ficha = ficha

        # Si se proporciona contraseña, actualizarla
        if password_aprendiz:
            aprendiz.password_aprendiz = generate_password_hash(password_aprendiz)

        try:
            db.session.commit()
            flash('✅ Aprendiz actualizado correctamente.', 'success')
            return redirect(url_for('aprendiz_bp.perfil_aprendiz'))  # Corregido: blueprint 'estudiantes'
        except IntegrityError:
            db.session.rollback()
            flash('⚠️ Documento, email o celular duplicado.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {str(e)}', 'danger')

    # Renderizar plantilla
    return render_template(
        'perfil_aprendiz.html',
        aprendiz=aprendiz,
        mode='edit',
        tipos_documento=tipos_documento,
        fichas=fichas
    )

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
    return redirect(url_for('estudiantes.listar_estudiantes'))  # Corregido: blueprint 'estudiantes'

# ---- PERFIL DEL APRENDIZ ----
@bp.route('/perfil')
@login_required
def perfil_aprendiz():
    if not hasattr(current_user, "id_aprendiz"):
        flash("No tienes permiso para acceder a este perfil.", "danger")
        return redirect(url_for("auth.dashboard"))
    return render_template("perfil_aprendiz.html", aprendiz=current_user)