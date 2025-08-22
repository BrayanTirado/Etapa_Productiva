from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.users import Aprendiz, Instructor   
from app import db
from sqlalchemy.exc import IntegrityError

# Blueprint para manejar autenticación (rutas bajo /auth)
bp = Blueprint('auth', __name__, url_prefix='/auth')

# --- LOGIN ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':  
        documento = request.form.get('documento')
        password_aprendiz = request.form.get('password_aprendiz')

        if not all([documento, password_aprendiz]):
            flash('El documento y la contraseña son obligatorios.', 'warning')
            return redirect(url_for('auth.login'))

        # Buscar primero en Aprendiz
        user = Aprendiz.query.filter_by(documento=documento).first()
        
        # Si no es Aprendiz, buscar en Instructor
        if not user:
            user = Instructor.query.filter_by(documento=documento).first()

        # Validar credenciales
        if user:
            password_field = 'password_aprendiz' if isinstance(user, Aprendiz) else 'passwordInstructor'
            if check_password_hash(getattr(user, password_field), password_aprendiz):
                login_user(user)
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('auth.dashboard'))
        flash('Documento o contraseña incorrectos.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('login.html')

# --- DASHBOARD ---
from datetime import datetime  

@bp.route('/dashboard')
@login_required
def dashboard():
    if isinstance(current_user, Aprendiz):
        return render_template('dasboardh_aprendiz.html', aprendiz=current_user)
    elif isinstance(current_user, Instructor):
        return render_template('dasboardh_instructor.html', instructor=current_user, current_year=datetime.now().year)


# --- LOGOUT ---
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


# --- REGISTRO DE APRENDIZ ---
@bp.route('/aprendiz', methods=['GET', 'POST'])
def aprendiz():
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

        # Validación de campos obligatorios
        if not all([nombre, apellido, tipo_documento, documento, email, celular, ficha, contrato_id_contrato, password_aprendiz]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('auth.aprendiz'))

        try:
            ficha = int(ficha)
            contrato_id_contrato = int(contrato_id_contrato)
        except ValueError:
            flash('La ficha y el ID del contrato deben ser números válidos.', 'danger')
            return redirect(url_for('auth.aprendiz'))

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

            # Opcional: loguear inmediatamente al aprendiz después de registrarse
            # login_user(nuevo)

            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un aprendiz con ese documento, email o celular.', 'danger')
            return redirect(url_for('auth.aprendiz'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el aprendiz: {str(e)}', 'danger')
            return redirect(url_for('auth.aprendiz'))

    return render_template('aprendiz.html')  # ⚠ template en minúscula para consistencia


# --- REGISTRO DE INSTRUCTOR ---
@bp.route('/instructor', methods=['GET', 'POST'])
def instructor():
    if request.method == 'POST':
        # 🔹 Usar los mismos nombres que los inputs en instructor.html
        nombre = request.form.get('nombre_instructor')
        apellido = request.form.get('apellido_instructor')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        correo = request.form.get('correo_instructor')
        celular = request.form.get('celular_instructor')
        password = request.form.get('passwordInstructor')

        # Validar que todos los campos estén completos
        if not all([nombre, apellido, tipo_documento, documento, correo, celular, password]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('auth.instructor'))

        # Generar hash de la contraseña
        hashed_password = generate_password_hash(password)

        # Crear nuevo instructor
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
            return redirect(url_for('auth.instructor'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el instructor: {str(e)}', 'danger')
            return redirect(url_for('auth.instructor'))

    return render_template('instructor.html')



