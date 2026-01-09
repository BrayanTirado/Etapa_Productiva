from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.users import Aprendiz, Instructor, Contrato, Programa, Administrador, AdministradorSede, Evidencia, PasswordResetToken, Notificacion, Ficha
from app import db
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from datetime import datetime, date, timedelta
import secrets
import re
import os

bp = Blueprint('auth', __name__, url_prefix='/auth')


# --- LOGIN GENERAL UNIFICADO ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirigir según rol
        if isinstance(current_user, Administrador):
            return redirect(url_for('adm_bp.dashboard'))
        elif isinstance(current_user, AdministradorSede):
            return redirect(url_for('adm_sede_bp.dashboard'))
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
                AdministradorSede.query.filter_by(documento=documento).first() or
                Instructor.query.filter_by(documento=documento).first() or
                Aprendiz.query.filter_by(documento=documento).first())

        if user:
            # Campo de contraseña según tipo
            if isinstance(user, (Administrador, AdministradorSede)):
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
                elif isinstance(user, AdministradorSede):
                    return redirect(url_for('adm_sede_bp.dashboard'))
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
        nombre = request.form.get('nombre').strip()
        apellido = request.form.get('apellido').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo').strip().lower()
        celular = request.form.get('celular').strip()
        password = request.form.get('password')
        ficha_numero = request.form.get('ficha').strip()
        confirmar_ficha = request.form.get('confirmar_ficha').strip()
        jornada = request.form.get('jornada').strip()

        if not all([nombre, apellido, tipo_documento, documento, correo, celular, password, ficha_numero, confirmar_ficha, jornada]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('auth.registro_aprendiz'))

        if ficha_numero != confirmar_ficha:
            flash('El número de ficha y la confirmación no coinciden.', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

        # Verificar ficha
        try:
            ficha_numero_int = int(ficha_numero)
        except ValueError:
            flash('El número de ficha debe ser un número válido.', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

        ficha = Ficha.query.filter_by(numero_ficha=ficha_numero_int).first()
        if not ficha:
            flash('El número de ficha no existe en el sistema.', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

        # Buscar programa asociado a la ficha
        programa = Programa.query.filter_by(ficha_id=ficha.id_ficha).first()
        if not programa:
            flash('No hay un programa asociado a esta ficha.', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

        # Obtener instructor y sede
        instructor = programa.instructor_rel
        sede = instructor.sede if instructor else None

        # Verificar unicidad global (todos los tipos de usuario)
        from app.models.users import Administrador, Instructor

        # Verificar documento en todos los modelos
        documento_existe = (Aprendiz.query.filter_by(documento=documento).first() or
                            Administrador.query.filter_by(documento=documento).first() or
                            Instructor.query.filter_by(documento=documento).first())

        # Verificar email (solo en modelos que tienen email)
        email_existe = (Aprendiz.query.filter_by(correo=correo).first() or
                        Instructor.query.filter_by(correo_instructor=correo).first())

        # Verificar celular (solo en modelos que tienen celular)
        celular_existe = (Aprendiz.query.filter_by(celular=celular).first() or
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
            correo=correo,
            celular=celular,
            jornada=jornada,
            password_aprendiz=hashed_password,
            programa_id=programa.id_programa,
            instructor_id=instructor.id_instructor if instructor else None,
            sede_id=sede.id_sede if sede else None
        )
        try:
            db.session.add(nuevo)
            db.session.commit()

            # Notificación al administrador principal
            mensaje_notificacion = f"El aprendiz {nuevo.nombre} {nuevo.apellido} se ha registrado exitosamente con ficha {ficha_numero_int}."

            # Buscar administradores para notificar
            administradores = Administrador.query.all()
            for admin in administradores:
                notificacion = Notificacion(
                    motivo="Registro de aprendiz",
                    mensaje=mensaje_notificacion,
                    remitente_id=nuevo.id_aprendiz,
                    rol_remitente="aprendiz",
                    destinatario_id=admin.id_admin,
                    rol_destinatario="administrador"
                )
                db.session.add(notificacion)

            db.session.commit()

            flash('Aprendiz registrado con éxito.', 'success')
            return render_template('aprendiz.html', now=datetime.now())
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el aprendiz: {str(e)}', 'danger')
            return redirect(url_for('auth.registro_aprendiz'))

    return render_template('aprendiz.html', now=datetime.now())


# --- REGISTRO DE INSTRUCTOR ---
@bp.route('/instructor', methods=['GET', 'POST'])
def instructor():
    from app.models.users import Sede  # Importar Sede aquí
    sedes = Sede.query.all()  # Definir sedes al inicio
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

        if token.fecha_expiracion.replace(tzinfo=None) < datetime.utcnow().replace(tzinfo=None):
            flash("El token ha expirado.", "danger")
            return redirect(url_for('auth.instructor'))

        # Verificar unicidad global (todos los tipos de usuario)
        from app.models.users import Administrador, Aprendiz

        # Verificar documento en todos los modelos
        documento_existe = (Instructor.query.filter_by(documento=documento).first() or
                            Administrador.query.filter_by(documento=documento).first() or
                            Aprendiz.query.filter_by(documento=documento).first())

        # Verificar email (solo en modelos que tienen email)
        email_existe = (Instructor.query.filter_by(correo_instructor=correo).first() or
                        Aprendiz.query.filter_by(correo=correo).first())

        # Verificar celular (solo en modelos que tienen celular)
        celular_existe = (Instructor.query.filter_by(celular_instructor=celular).first() or
                          Aprendiz.query.filter_by(celular=celular).first())

        if documento_existe:
            flash('Error: Ya existe un usuario con ese documento.', 'danger')
            return redirect(url_for('auth.instructor'))

        if email_existe:
            flash('Error: Ya existe un usuario con ese correo.', 'danger')
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
            sede_id=sede_id_final
        )

        try:
            db.session.add(nuevo)
            db.session.commit()

            # Notificación a administradores
            administradores = Administrador.query.all()
            for admin in administradores:
                noti = Notificacion(
                    motivo="Se ha registrado un nuevo Instructor",
                    mensaje=f"{nuevo.nombre_instructor} {nuevo.apellido_instructor} en la sede {sede.nombre_sede}",
                    remitente_id=nuevo.id_instructor,
                    rol_remitente="Instructor",
                    destinatario_id=admin.id_admin,
                    rol_destinatario="administrador",
                    visto=False
                )
                db.session.add(noti)
            db.session.commit()

            flash('Instructor creado exitosamente.', 'success')
            return render_template('instructor.html', sedes=sedes)
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el instructor: {str(e)}', 'danger')
            return redirect(url_for('auth.instructor'))

    return render_template('instructor.html', sedes=sedes)


# --- FUNCIONES AUXILIARES PARA RECUPERACIÓN DE CONTRASEÑA ---

def generate_reset_token():
    """Genera un token único para recuperación de contraseña"""
    return secrets.token_urlsafe(32)

def find_user_by_email(email):
    """Busca un usuario por email en todos los tipos de usuario"""
    # Buscar en Aprendiz
    user = Aprendiz.query.filter_by(correo=email).first()
    if user:
        return user, 'aprendiz'

    # Buscar en Instructor
    user = Instructor.query.filter_by(correo_instructor=email).first()
    if user:
        return user, 'instructor'

    # Eliminado: Coordinador ya no existe

    # Buscar en Administrador
    user = Administrador.query.filter_by(correo=email).first()
    if user:
        return user, 'administrador'

    return None, None

def send_reset_email(email, reset_url):
    """Envía el email de recuperación de contraseña usando SMTP"""
    from flask import current_app
    from flask_mail import Message, Mail
    import os

    # Verificar configuración de email
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_port = current_app.config.get('MAIL_PORT')
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD')
    mail_default_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
    mail_use_ssl = current_app.config.get('MAIL_USE_SSL')
    mail_use_tls = current_app.config.get('MAIL_USE_TLS')

    # Verificar que tengamos las credenciales necesarias
    if not mail_username or not mail_password:
        return False

    try:
        # Crear instancia de Mail si no existe
        mail = Mail(current_app)

        msg = Message(
            subject='Recuperación de contraseña - SENA',
            recipients=[email],
            sender=mail_default_sender,
            body=f"""
Hola,

Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para continuar:

{reset_url}

Este enlace expirará en 1 hora.

Si no solicitaste este cambio, ignora este mensaje.

Atentamente,
Sistema SENA
            """.strip()
        )

        mail.send(msg)
        return True

    except Exception as e:
        return False

# --- RUTAS PARA RECUPERACIÓN DE CONTRASEÑA ---


@bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Página para solicitar recuperación de contraseña"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Por favor ingresa tu correo electrónico.', 'warning')
            return redirect(url_for('auth.forgot_password'))

        # Validar formato de email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Por favor ingresa un correo electrónico válido.', 'warning')
            return redirect(url_for('auth.forgot_password'))

        # Buscar usuario por email
        user, user_type = find_user_by_email(email)

        if not user:
            # Por seguridad, no revelamos si el email existe o no
            flash('Si tu correo electrónico está registrado, recibirás un enlace para restablecer tu contraseña.', 'info')
            return redirect(url_for('auth.login'))

        # Generar token
        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)  # Expira en 1 hora

        # Crear registro del token
        # Mapeo de atributos de ID por tipo de usuario
        id_attr_map = {
            'aprendiz': 'id_aprendiz',
            'instructor': 'id_instructor',
            'administrador': 'id_admin'
        }
        id_attr = id_attr_map.get(user_type, f'id_{user_type}')
        user_id = getattr(user, id_attr)

        reset_token = PasswordResetToken(
            token=token,
            email=email,
            user_type=user_type,
            user_id=user_id,
            expires_at=expires_at
        )

        try:
            # Verificar que la tabla existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'password_reset_token' not in tables:
                db.create_all()

            db.session.add(reset_token)
            db.session.commit()

            # Generar URL de restablecimiento
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            # Enviar email
            email_sent = send_reset_email(email, reset_url)

            if email_sent:
                flash('Si tu correo electrónico está registrado, recibirás un enlace para restablecer tu contraseña.', 'info')
            else:
                flash('Hemos procesado tu solicitud, pero puede haber un problema temporal con el envío de emails. Contacta al administrador si no recibes el mensaje.', 'warning')

            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('Error al procesar la solicitud. Inténtalo de nuevo.', 'danger')
            return redirect(url_for('auth.forgot_password'))

    return render_template('forgot_password.html', now=datetime.now())


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Página para restablecer contraseña usando token"""
    import time
    start_time = time.time()

    # Validar que el token no esté vacío
    if not token or len(token.strip()) == 0:
        flash('El enlace de restablecimiento no es válido o ha expirado.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        # Verificar conexión a BD con timeout
        db_start = time.time()

        # Consulta simple para verificar conexión
        from sqlalchemy import text
        db.session.execute(text("SELECT 1")).first()
        db_time = time.time() - db_start

        # Buscar token válido con timeout y optimización
        search_start = time.time()

        reset_token = None

        # Intentar múltiples veces con reintentos para manejar problemas de conectividad
        max_retries = 3
        retry_delay = 1  # segundos

        for attempt in range(max_retries):
            try:
                # Usar consulta optimizada con timeout
                from sqlalchemy import text

                # Ejecutar consulta con timeout usando SQL directo para mejor control
                query = text("""
                    SELECT id, token, email, user_type, user_id, created_at, expires_at, used
                    FROM password_reset_token
                    WHERE token = :token AND used = 0
                    LIMIT 1
                """)

                # Ejecutar con timeout
                result = db.session.execute(query, {'token': token}).first()

                if result:
                    # Convertir resultado a objeto PasswordResetToken
                    reset_token = PasswordResetToken(
                        id=result[0],
                        token=result[1],
                        email=result[2],
                        user_type=result[3],
                        user_id=result[4],
                        created_at=result[5],
                        expires_at=result[6],
                        used=result[7]
                    )
                    break
                else:
                    reset_token = None
                    break

            except Exception as query_error:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue

                # Fallback a consulta ORM en el último intento
                try:
                    reset_token = (PasswordResetToken.query
                                  .filter(PasswordResetToken.token == token)
                                  .filter(PasswordResetToken.used == False)
                                  .first())
                    break
                except Exception as orm_error:
                    reset_token = None
                    break

        search_time = time.time() - search_start

        # Verificar si la búsqueda tomó demasiado tiempo
        if search_time > 30:  # Más de 30 segundos - timeout crítico
            flash('La conexión está tardando demasiado. Inténtalo de nuevo en unos minutos.', 'warning')
            return redirect(url_for('auth.login'))

        if not reset_token:
            # Verificar si existe pero está usado (consulta optimizada)
            used_token = PasswordResetToken.query.filter_by(token=token).first()
            if used_token:
                if used_token.used:
                    flash('Este enlace de restablecimiento ya ha sido utilizado.', 'danger')
                else:
                    flash('Error interno del sistema. Inténtalo de nuevo.', 'danger')
            else:
                flash('El enlace de restablecimiento no es válido o ha expirado.', 'danger')
            return redirect(url_for('auth.login'))

        # Verificar expiración con más detalle
        is_expired = reset_token.is_expired()

        if is_expired:
            flash('El enlace de restablecimiento ha expirado. Solicita uno nuevo.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        total_time = time.time() - start_time

    except Exception as db_error:
        error_time = time.time() - start_time

        # Intentar rollback si es necesario
        try:
            db.session.rollback()
        except:
            pass

        flash('Error interno del servidor. La conexión está tardando demasiado. Inténtalo de nuevo.', 'danger')
        return redirect(url_for('auth.login'))

    # Verificar expiración con más detalle
    is_expired = reset_token.is_expired()

    if is_expired:
        flash('El enlace de restablecimiento ha expirado. Solicita uno nuevo.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            flash('Por favor completa todos los campos.', 'warning')
            return redirect(url_for('auth.reset_password', token=token))

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'warning')
            return redirect(url_for('auth.reset_password', token=token))

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'warning')
            return redirect(url_for('auth.reset_password', token=token))

        # Buscar usuario según tipo
        user = None
        if reset_token.user_type == 'aprendiz':
            user = Aprendiz.query.get(reset_token.user_id)
            password_field = 'password_aprendiz'
        elif reset_token.user_type == 'instructor':
            user = Instructor.query.get(reset_token.user_id)
            password_field = 'password_instructor'
        elif reset_token.user_type == 'administrador':
            user = Administrador.query.get(reset_token.user_id)
            password_field = 'password'

        if not user:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('auth.login'))

        try:
            # Usar transacción para evitar problemas de concurrencia
            # Verificar nuevamente que el token no haya sido usado por otro usuario
            if reset_token.used:
                print(f"[ERROR] Token ya fue usado durante el procesamiento")
                flash('Este enlace ya ha sido utilizado por otro usuario.', 'danger')
                return redirect(url_for('auth.login'))

            # Actualizar contraseña
            hashed_password = generate_password_hash(password)
            setattr(user, password_field, hashed_password)

            # Marcar token como usado
            reset_token.used = True

            db.session.commit()

            flash('Tu contraseña ha sido restablecida exitosamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('Error al restablecer la contraseña. Inténtalo de nuevo.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

    return render_template('reset_password.html', token=token, now=datetime.now())
