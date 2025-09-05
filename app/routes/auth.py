from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.users import Aprendiz, Instructor, Contrato, Programa
from app import db
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date  

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
@bp.route('/dashboard')
@login_required
def dashboard():

    # --- Dashboard Aprendiz ---
    if isinstance(current_user, Aprendiz):
        aprendiz = current_user

        # Progreso de evidencias
        total_requerido = 17
        evidencias_subidas = len(aprendiz.evidencias)
        progreso = int((evidencias_subidas / total_requerido) * 100) if total_requerido > 0 else 0

        # Progreso de tiempo contrato
        contrato = aprendiz.contrato
        progreso_tiempo = 0
        if contrato and contrato.fecha_inicio and contrato.fecha_fin:
            fecha_inicio = contrato.fecha_inicio.date() if hasattr(contrato.fecha_inicio, "date") else contrato.fecha_inicio
            fecha_fin = contrato.fecha_fin.date() if hasattr(contrato.fecha_fin, "date") else contrato.fecha_fin

            total_dias = (fecha_fin - fecha_inicio).days
            dias_transcurridos = (date.today() - fecha_inicio).days

            if total_dias > 0:
                progreso_tiempo = round((dias_transcurridos / total_dias) * 100, 2)
                progreso_tiempo = min(max(progreso_tiempo, 0), 100)

        return render_template(
            'dasboardh_aprendiz.html',
            aprendiz=aprendiz,
            progreso=progreso,
            progreso_tiempo=progreso_tiempo,
            contrato=contrato
        )

    # --- Dashboard Instructor ---
    elif isinstance(current_user, Instructor):
        aprendices_finalizan = (
            db.session.query(Aprendiz, Contrato, Programa)
            .join(Contrato, Aprendiz.contrato_id == Contrato.id_contrato)
            .join(Programa, Aprendiz.programa_id == Programa.id_programa)
            .filter(Contrato.fecha_fin.isnot(None))
            .all()
        )

        eventos = []
        for aprendiz, contrato, programa in aprendices_finalizan:
            eventos.append({
                "fecha_fin": contrato.fecha_fin.strftime("%Y-%m-%d"),
                "fecha_inicio": contrato.fecha_inicio.strftime("%Y-%m-%d"),
                "nombre": f"{aprendiz.nombre} {aprendiz.apellido}",
                "ficha": programa.ficha
            })

        return render_template(
            'dasboardh_instructor.html',
            instructor=current_user,
            eventos=eventos,
            current_year=datetime.now().year
        )

    # --- Usuario no permitido ---
    else:
        flash("No tienes permisos para acceder al dashboard.", "danger")
        return redirect(url_for("auth.login"))


# --- LOGOUT ---
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


# --- REGISTRO DE APRENDIZ ---
@bp.route('/aprendiz', methods=['GET', 'POST'])
def registro_aprendiz():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        email = request.form.get('email')
        celular = request.form.get('celular')
        password_aprendiz = request.form.get('password_aprendiz')

        if not all([nombre, apellido, tipo_documento, documento, email, celular, password_aprendiz]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('auth.registro_aprendiz'))

        hashed_password = generate_password_hash(password_aprendiz)

        nuevo = Aprendiz(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            email=email,
            celular=celular,
            password_aprendiz=hashed_password
        )

        try:
            db.session.add(nuevo)
            db.session.commit()
            flash('Aprendiz creado exitosamente.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un aprendiz con ese documento, email o celular.', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el aprendiz: {str(e)}', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

    return render_template('aprendiz.html')


# --- REGISTRO DE INSTRUCTOR ---
@bp.route('/instructor', methods=['GET', 'POST'])
def instructor():
    if request.method == 'POST':
        nombre = request.form.get('nombre_instructor')
        apellido = request.form.get('apellido_instructor')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        correo = request.form.get('correo_instructor')
        celular = request.form.get('celular_instructor')
        password = request.form.get('passwordInstructor')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular, password]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('auth.instructor'))

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
            return redirect(url_for('auth.instructor'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el instructor: {str(e)}', 'danger')
            return redirect(url_for('auth.instructor'))

    return render_template('instructor.html')
