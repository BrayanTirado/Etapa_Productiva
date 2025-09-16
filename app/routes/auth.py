from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.users import Aprendiz, Instructor, Contrato, Programa, Coordinador, Administrador, Evidencia
from app import db
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from datetime import datetime, date  

bp = Blueprint('auth', __name__, url_prefix='/auth')


# --- LOGIN GENERAL UNIFICADO ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirigir según rol
        if isinstance(current_user, Administrador):
            return redirect(url_for('adm_bp.dashboard'))
        elif isinstance(current_user, Coordinador):
            return redirect(url_for('coordinador_bp.dashboard'))
        elif isinstance(current_user, Instructor):
            return redirect(url_for('instructor_bp.dashboard_instructor', instructor_id=current_user.id_instructor))
        elif isinstance(current_user, Aprendiz):
            return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))
        else:
            return redirect(url_for('auth.login'))

    if request.method == 'POST':
        documento = request.form.get('documento', '').strip()
        password = request.form.get('password', '')

        if not documento or not password:
            flash('El documento y la contraseña son obligatorios.', 'warning')
            return redirect(url_for('auth.login'))

        # Buscar usuario en todos los roles
        user = (Administrador.query.filter_by(documento=documento).first() or
                Coordinador.query.filter_by(documento=documento).first() or
                Instructor.query.filter_by(documento=documento).first() or
                Aprendiz.query.filter_by(documento=documento).first())

        if user:
            # Campo de contraseña según tipo
            if isinstance(user, (Administrador, Coordinador)):
                password_field = 'password'
            elif isinstance(user, Instructor):
                password_field = 'password_instructor'
            else:  # Aprendiz
                password_field = 'password_aprendiz'

            if check_password_hash(getattr(user, password_field), password):
                login_user(user)
                flash('Inicio de sesión exitoso', 'success')

                # Redirigir según rol
                if isinstance(user, Administrador):
                    return redirect(url_for('adm_bp.dashboard'))
                elif isinstance(user, Coordinador):
                    return redirect(url_for('coordinador_bp.dashboard'))
                elif isinstance(user, Instructor):
                    return redirect(url_for('instructor_bp.dashboard_instructor', instructor_id=user.id_instructor))
                else:  # Aprendiz
                    return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))

        flash('Documento o contraseña incorrectos.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('login.html', now=datetime.now())



# --- DASHBOARD GENERAL PARA INSTRUCTOR Y APRENDIZ ---
@bp.route('/dashboard')
@login_required
def dashboard():
    if isinstance(current_user, Aprendiz):
        aprendiz = current_user
        total_requerido = 17

        # Contar solo evidencias realmente subidas
        evidencias_subidas = (
            db.session.query(Evidencia)
            .filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz)
            .filter(Evidencia.fecha_subida.isnot(None), Evidencia.url_archivo != '')
            .count()
        )

        progreso = int((evidencias_subidas / total_requerido) * 100) if total_requerido > 0 else 0

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
            contrato=contrato,
            now=datetime.now()
        )

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
            now=datetime.now()
        )

    elif isinstance(current_user, Coordinador):
        return redirect(url_for('coordinador_bp.dashboard'))

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
    from app.models.users import Sede  # Importar Sede aquí
    if request.method == 'POST':
        nombre = request.form.get('nombre').strip()
        apellido = request.form.get('apellido').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        email = request.form.get('email').strip().lower()
        celular = request.form.get('celular').strip()
        password = request.form.get('password')
        sede_nombre = request.form.get('sede_id')

        if not all([nombre, apellido, tipo_documento, documento, email, celular, password, sede_nombre]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('auth.registro_aprendiz'))

        # Buscar la sede por nombre
        sede = Sede.query.filter_by(nombre_sede=sede_nombre).first()
        if not sede:
            flash('La sede seleccionada no existe en el sistema.', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

        # Verificar unicidad global (todos los tipos de usuario)
        from app.models.users import Administrador, Coordinador, Instructor

        # Verificar documento en todos los modelos
        documento_existe = (Aprendiz.query.filter_by(documento=documento).first() or
                            Administrador.query.filter_by(documento=documento).first() or
                            Coordinador.query.filter_by(documento=documento).first() or
                            Instructor.query.filter_by(documento=documento).first())

        # Verificar email (solo en modelos que tienen email)
        email_existe = (Aprendiz.query.filter_by(email=email).first() or
                        Coordinador.query.filter_by(correo=email).first() or
                        Instructor.query.filter_by(correo_instructor=email).first())

        # Verificar celular (solo en modelos que tienen celular)
        celular_existe = (Aprendiz.query.filter_by(celular=celular).first() or
                          Coordinador.query.filter_by(celular=celular).first() or
                          Instructor.query.filter_by(celular_instructor=celular).first())

        if documento_existe:
            flash('Error: Ya existe un usuario con ese documento.', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

        if email_existe:
            flash('Error: Ya existe un usuario con ese email.', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

        if celular_existe:
            flash('Error: Ya existe un usuario con ese número de celular.', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

        hashed_password = generate_password_hash(password)
        nuevo = Aprendiz(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            email=email,
            celular=celular,
            password_aprendiz=hashed_password,
            sede_id=sede.id_sede
        )
        try:
            db.session.add(nuevo)
            db.session.commit()
            flash('Aprendiz creado exitosamente.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el aprendiz: {str(e)}', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

    sedes = Sede.query.all()
    return render_template('aprendiz.html', sedes=sedes, now=datetime.now())


# --- REGISTRO DE INSTRUCTOR ---
@bp.route('/instructor', methods=['GET', 'POST'])
def instructor():
    from app.models.users import Sede  # Importar Sede aquí
    if request.method == 'POST':
        token_input = request.form.get('token').strip()
        nombre = request.form.get('nombre_instructor').strip()
        apellido = request.form.get('apellido_instructor').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo_instructor').strip().lower()
        celular = request.form.get('celular_instructor').strip()
        password = request.form.get('password')
        sede_nombre = request.form.get('sede_id')

        if not all([token_input, nombre, apellido, tipo_documento, documento, correo, celular, password, sede_nombre]):
            flash('Todos los campos son obligatorios, incluido el token.', 'warning')
            return redirect(url_for('auth.instructor'))

        # Buscar la sede por nombre
        sede = Sede.query.filter_by(nombre_sede=sede_nombre).first()
        if not sede:
            flash('La sede seleccionada no existe en el sistema.', 'danger')
            return redirect(url_for('auth.instructor'))

        # Verificar token válido
        from app.models.users import TokenInstructor  # Importar aquí para evitar ciclos
        token = TokenInstructor.query.filter_by(token=token_input, activo=True).first()

        if not token:
            flash("El token no es válido.", "danger")
            return redirect(url_for('auth.instructor'))

        if token.fecha_expiracion < datetime.utcnow():
            flash("El token ha expirado.", "danger")
            return redirect(url_for('auth.instructor'))

        # Verificar unicidad global (todos los tipos de usuario)
        from app.models.users import Administrador, Coordinador, Aprendiz

        # Verificar documento en todos los modelos
        documento_existe = (Instructor.query.filter_by(documento=documento).first() or
                            Administrador.query.filter_by(documento=documento).first() or
                            Coordinador.query.filter_by(documento=documento).first() or
                            Aprendiz.query.filter_by(documento=documento).first())

        # Verificar email (solo en modelos que tienen email)
        email_existe = (Instructor.query.filter_by(correo_instructor=correo).first() or
                        Coordinador.query.filter_by(correo=correo).first() or
                        Aprendiz.query.filter_by(email=correo).first())

        # Verificar celular (solo en modelos que tienen celular)
        celular_existe = (Instructor.query.filter_by(celular_instructor=celular).first() or
                          Coordinador.query.filter_by(celular=celular).first() or
                          Aprendiz.query.filter_by(celular=celular).first())

        if documento_existe:
            flash('Error: Ya existe un usuario con ese documento.', 'danger')
            return redirect(url_for('auth.instructor'))

        if email_existe:
            flash('Error: Ya existe un usuario con ese email.', 'danger')
            return redirect(url_for('auth.instructor'))

        if celular_existe:
            flash('Error: Ya existe un usuario con ese número de celular.', 'danger')
            return redirect(url_for('auth.instructor'))

        hashed_password = generate_password_hash(password)
        # Usar sede del formulario si se proporciona, sino la del token
        sede_id_final = sede.id_sede if sede else token.sede_id

        nuevo = Instructor(
            nombre_instructor=nombre,
            apellido_instructor=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            correo_instructor=correo,
            celular_instructor=celular,
            password_instructor=hashed_password,
            coordinador_id=token.coordinador_id,
            sede_id=sede_id_final
        )

        try:
            db.session.add(nuevo)
            db.session.commit()
            flash('Instructor creado exitosamente.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el instructor: {str(e)}', 'danger')
            return redirect(url_for('auth.instructor'))

    sedes = Sede.query.all()
    return render_template('instructor.html', sedes=sedes)
