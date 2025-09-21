from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.users import Aprendiz, Instructor, Contrato, Programa, Coordinador, Administrador, Evidencia, PasswordResetToken
from app import db, mail
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

        if token.fecha_expiracion.replace(tzinfo=None) < datetime.utcnow().replace(tzinfo=None):
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


# --- FUNCIONES AUXILIARES PARA RECUPERACIÓN DE CONTRASEÑA ---

def test_email_connection():
    """Prueba la conexión SMTP para diagnosticar problemas de email"""
    from flask import current_app
    import smtplib

    print("=" * 60)
    print("PRUEBA DE CONEXIÓN SMTP")
    print("=" * 60)

    # Función auxiliar para obtener configuración con fallback
    def get_mail_config(key, default=None):
        value = current_app.config.get(key)
        if value is None:
            # Intentar cargar desde .env si no está en config
            from dotenv import load_dotenv
            load_dotenv()
            value = os.environ.get(key, default)
        return value

    server = get_mail_config('MAIL_SERVER', 'smtp.gmail.com')
    port = get_mail_config('MAIL_PORT', 587)
    username = get_mail_config('MAIL_USERNAME')
    password = get_mail_config('MAIL_PASSWORD')
    use_tls = get_mail_config('MAIL_USE_TLS', True)
    use_ssl = get_mail_config('MAIL_USE_SSL', False)

    print(f"Servidor: {server}")
    print(f"Puerto: {port}")
    print(f"Usuario: {username}")
    print(f"Usar TLS: {use_tls}")
    print(f"Usar SSL: {use_ssl}")
    print()

    try:
        print("Intentando conectar al servidor SMTP...")

        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port)
        else:
            smtp = smtplib.SMTP(server, port)

        print("[OK] Conexión inicial exitosa")

        if use_tls:
            smtp.starttls()
            print("[OK] TLS iniciado correctamente")

        if username and password:
            smtp.login(username, password)
            print("[OK] Autenticación exitosa")

        smtp.quit()
        print("[OK] Conexión cerrada correctamente")
        print("[OK] PRUEBA DE CONEXIÓN SMTP EXITOSA")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERROR] Error de autenticación: {e}")
        print("   Verifica que el usuario y contraseña sean correctos")
        print("   Para Gmail, usa una contraseña de aplicación")
    except smtplib.SMTPConnectError as e:
        print(f"[ERROR] Error de conexión: {e}")
        print("   Verifica que el servidor tenga acceso a internet")
        print(f"   Verifica que el puerto {port} no esté bloqueado")
    except smtplib.SMTPException as e:
        print(f"[ERROR] Error SMTP: {e}")
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

    print("[ERROR] PRUEBA DE CONEXIÓN SMTP FALLIDA")
    return False

def generate_reset_token():
    """Genera un token único para recuperación de contraseña"""
    return secrets.token_urlsafe(32)

def find_user_by_email(email):
    """Busca un usuario por email en todos los tipos de usuario"""
    # Buscar en Aprendiz
    user = Aprendiz.query.filter_by(email=email).first()
    if user:
        return user, 'aprendiz'

    # Buscar en Instructor
    user = Instructor.query.filter_by(correo_instructor=email).first()
    if user:
        return user, 'instructor'

    # Buscar en Coordinador
    user = Coordinador.query.filter_by(correo=email).first()
    if user:
        return user, 'coordinador'

    # Buscar en Administrador
    user = Administrador.query.filter_by(correo=email).first()
    if user:
        return user, 'administrador'

    return None, None

def send_reset_email(email, reset_url):
    """Envía el email de recuperación de contraseña"""
    print(f"[EMAIL] Iniciando envío de email a {email}")
    print(f"[EMAIL] URL de restablecimiento: {reset_url}")

    # Verificar configuración de email con fallback robusto
    from flask import current_app
    mail_config = current_app.config

    # Función auxiliar para obtener configuración con fallback
    def get_mail_config(key, default=None):
        value = mail_config.get(key)
        if value is None:
            # Intentar cargar desde .env si no está en config
            from dotenv import load_dotenv
            load_dotenv()
            value = os.environ.get(key, default)
        return value

    # Obtener configuración con fallback
    mail_server = get_mail_config('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = get_mail_config('MAIL_PORT', 587)
    mail_username = get_mail_config('MAIL_USERNAME')
    mail_password = get_mail_config('MAIL_PASSWORD')
    mail_default_sender = get_mail_config('MAIL_DEFAULT_SENDER', mail_username)
    mail_use_tls = get_mail_config('MAIL_USE_TLS', True)
    mail_use_ssl = get_mail_config('MAIL_USE_SSL', False)

    print(f"[EMAIL] Configuración de mail:")
    print(f"[EMAIL]   MAIL_SERVER: {mail_server}")
    print(f"[EMAIL]   MAIL_PORT: {mail_port}")
    print(f"[EMAIL]   MAIL_USE_TLS: {mail_use_tls}")
    print(f"[EMAIL]   MAIL_USE_SSL: {mail_use_ssl}")
    print(f"[EMAIL]   MAIL_USERNAME: {mail_username}")
    print(f"[EMAIL]   MAIL_DEFAULT_SENDER: {mail_default_sender}")

    try:
        # Crear mensaje usando configuración obtenida
        from flask_mail import Message as MailMessage

        msg = MailMessage(
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

        print(f"[EMAIL] Mensaje creado correctamente")
        print(f"[EMAIL] Enviando email...")

        # Enviar usando configuración directa si es necesario
        if hasattr(mail, 'send'):
            mail.send(msg)
        else:
            # Fallback: enviar directamente con smtplib
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            message = MIMEMultipart()
            message['From'] = mail_default_sender
            message['To'] = email
            message['Subject'] = 'Recuperación de contraseña - SENA'

            body = f"""
Hola,

Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para continuar:

{reset_url}

Este enlace expirará en 1 hora.

Si no solicitaste este cambio, ignora este mensaje.

Atentamente,
Sistema SENA
            """.strip()

            message.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(mail_server, mail_port)
            if mail_use_tls:
                server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_default_sender, email, message.as_string())
            server.quit()

        print(f"[EMAIL] [OK] Email enviado exitosamente a {email}")
        return True

    except Exception as e:
        print(f"[EMAIL] [ERROR] Error al enviar email a {email}: {e}")
        print(f"[EMAIL] Tipo de error: {type(e).__name__}")

        # Intentar diagnosticar el problema
        if "SMTP" in str(e):
            print(f"[EMAIL] Parece ser un problema de conexión SMTP")
            print(f"[EMAIL] Verifica que el servidor tenga acceso a internet")
            print(f"[EMAIL] Verifica que el puerto 587 no esté bloqueado")
        elif "authentication" in str(e).lower():
            print(f"[EMAIL] Problema de autenticación")
            print(f"[EMAIL] Verifica que MAIL_USERNAME y MAIL_PASSWORD sean correctos")
            print(f"[EMAIL] Para Gmail, asegúrate de usar una contraseña de aplicación")
        elif "connection" in str(e).lower():
            print(f"[EMAIL] Problema de conexión")
            print(f"[EMAIL] Verifica la conectividad a internet del servidor")

        import traceback
        print(f"[EMAIL] Traceback completo:")
        print(f"[EMAIL] {traceback.format_exc()}")

        return False

# --- RUTAS PARA RECUPERACIÓN DE CONTRASEÑA ---

@bp.route('/test_email')
@login_required
def test_email():
    """Ruta de prueba para verificar la conexión SMTP y envío de emails"""
    from flask import flash, redirect, url_for, current_app

    print("\n" + "="*60)
    print("INICIANDO PRUEBA DE EMAIL DESDE NAVEGADOR")
    print("="*60)

    # Primero probar conexión
    connection_ok = test_email_connection()

    if not connection_ok:
        flash('[ERROR] Prueba de conexión SMTP fallida. Revisa los logs para más detalles.', 'danger')
        return redirect(url_for('auth.login'))

    # Si la conexión funciona, probar envío de email de prueba
    print("\n" + "="*40)
    print("PROBANDO ENVÍO DE EMAIL DE PRUEBA")
    print("="*40)

    # Verificar configuración de email con fallback
    test_email_address = current_app.config.get('MAIL_DEFAULT_SENDER')

    # Si no está en config, intentar obtener de variables de entorno directamente
    if not test_email_address:
        from dotenv import load_dotenv
        load_dotenv()  # Cargar .env si no se cargó
        test_email_address = os.environ.get('MAIL_DEFAULT_SENDER')

    # Si aún no está disponible, usar MAIL_USERNAME como fallback
    if not test_email_address:
        test_email_address = current_app.config.get('MAIL_USERNAME') or os.environ.get('MAIL_USERNAME')

    if not test_email_address:
        print("[ERROR] Variables de email no disponibles:")
        print(f"  current_app.config.get('MAIL_DEFAULT_SENDER'): {current_app.config.get('MAIL_DEFAULT_SENDER')}")
        print(f"  os.environ.get('MAIL_DEFAULT_SENDER'): {os.environ.get('MAIL_DEFAULT_SENDER')}")
        print(f"  current_app.config.get('MAIL_USERNAME'): {current_app.config.get('MAIL_USERNAME')}")
        print(f"  os.environ.get('MAIL_USERNAME'): {os.environ.get('MAIL_USERNAME')}")
        flash('[ERROR] No se puede enviar email de prueba: Configuración de email no disponible.', 'danger')
        return redirect(url_for('auth.login'))

    test_url = url_for('auth.login', _external=True)
    success = send_reset_email(test_email_address, test_url)

    if success:
        flash('[OK] Prueba completa exitosa. Se envió un email de prueba.', 'success')
    else:
        flash('[ERROR] La conexión SMTP funciona pero el envío de email falló. Revisa los logs.', 'warning')

    return redirect(url_for('auth.login'))

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

        print(f"[KEY] Generando token para {email} (tipo: {user_type})")
        print(f"[TIME] Token expira: {expires_at}")

        # Crear registro del token
        # Mapeo de atributos de ID por tipo de usuario
        id_attr_map = {
            'aprendiz': 'id_aprendiz',
            'instructor': 'id_instructor',
            'coordinador': 'id_coordinador',
            'administrador': 'id_admin'
        }
        id_attr = id_attr_map.get(user_type, f'id_{user_type}')
        user_id = getattr(user, id_attr)

        print(f"[USER] User ID: {user_id} (atributo: {id_attr})")

        reset_token = PasswordResetToken(
            token=token,
            email=email,
            user_type=user_type,
            user_id=user_id,
            expires_at=expires_at
        )

        try:
            print(f"[SAVE] Guardando token en BD...")

            # Verificar que la tabla existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'password_reset_token' not in tables:
                print(f"[ERROR] ERROR: Tabla 'password_reset_token' no existe")
                print(f"[LIST] Tablas disponibles: {tables}")
                db.create_all()
                print(f"[TOOLS] Tablas creadas")

            db.session.add(reset_token)
            db.session.commit()
            print(f"[OK] Token guardado exitosamente - ID: {reset_token.id}")

            # Verificar que se guardó correctamente
            saved_token = PasswordResetToken.query.filter_by(token=token).first()
            if saved_token:
                print(f"[SEARCH] Verificación: Token encontrado en BD - ID: {saved_token.id}")
                print(f"   Token: {saved_token.token}")
                print(f"   Email: {saved_token.email}")
                print(f"   Expires: {saved_token.expires_at}")
            else:
                print(f"[ERROR] ERROR: Token no se encontró después del commit")

            # Generar URL de restablecimiento
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            print(f"[LINK] URL generada: {reset_url}")

            # Enviar email
            email_sent = send_reset_email(email, reset_url)

            if email_sent:
                print(f"[SUCCESS] Proceso de recuperación completado exitosamente para {email}")
                flash('Si tu correo electrónico está registrado, recibirás un enlace para restablecer tu contraseña.', 'info')
            else:
                print(f"[WARNING] Email no pudo enviarse, pero token guardado para {email}")
                flash('Hemos procesado tu solicitud, pero puede haber un problema temporal con el envío de emails. Contacta al administrador si no recibes el mensaje.', 'warning')

            return redirect(url_for('auth.login'))

        except Exception as e:
            print(f"[ERROR] ERROR al guardar token: {e}")
            print(f"[SEARCH] Tipo de error: {type(e).__name__}")
            import traceback
            print(f"[SEARCH] Traceback: {traceback.format_exc()}")
            db.session.rollback()
            flash('Error al procesar la solicitud. Inténtalo de nuevo.', 'danger')
            return redirect(url_for('auth.forgot_password'))

    return render_template('forgot_password.html', now=datetime.now())


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Página para restablecer contraseña usando token"""
    import time
    start_time = time.time()

    print(f"[SEARCH] Validando token: {token[:20]}...")
    print(f"[RULER] Longitud del token: {len(token)}")

    # Validar que el token no esté vacío
    if not token or len(token.strip()) == 0:
        print("[ERROR] Token vacío o inválido")
        flash('El enlace de restablecimiento no es válido o ha expirado.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        # Verificar conexión a BD con timeout
        print("[PLUG] Verificando conexión a BD...")
        db_start = time.time()

        # Consulta simple para verificar conexión
        from sqlalchemy import text
        db.session.execute(text("SELECT 1")).first()
        db_time = time.time() - db_start
        print(f"[OK] Conexión a BD verificada en {db_time:.2f}s")

        # Buscar token válido con timeout y optimización
        print("[SEARCH] Buscando token en BD...")
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
                    print(f"[OK] Token encontrado en intento {attempt + 1}")
                    break
                else:
                    reset_token = None
                    break

            except Exception as query_error:
                print(f"[ERROR] Error en consulta SQL (intento {attempt + 1}): {query_error}")
                if attempt < max_retries - 1:
                    print(f"[INFO] Reintentando en {retry_delay} segundos...")
                    import time
                    time.sleep(retry_delay)
                    continue

                # Fallback a consulta ORM en el último intento
                try:
                    reset_token = (PasswordResetToken.query
                                  .filter(PasswordResetToken.token == token)
                                  .filter(PasswordResetToken.used == False)
                                  .first())
                    print("[OK] Fallback a consulta ORM exitoso")
                    break
                except Exception as orm_error:
                    print(f"[ERROR] Error en consulta ORM fallback: {orm_error}")
                    reset_token = None
                    break

        search_time = time.time() - search_start
        print(f"[SEARCH] Búsqueda completada en {search_time:.2f}s")

        # Verificar si la búsqueda tomó demasiado tiempo
        if search_time > 10:  # Más de 10 segundos
            print(f"[WARNING] ADVERTENCIA: Búsqueda lenta ({search_time:.2f}s)")
            print("   Posible problema de conectividad con la BD remota")
            print(f"[WARNING] Token: {token[:20]}...")
            print(f"[WARNING] Current time: {datetime.utcnow()}")
        elif search_time > 30:  # Más de 30 segundos - timeout crítico
            print(f"[ERROR] ERROR: Búsqueda muy lenta ({search_time:.2f}s) - Timeout")
            print(f"[ERROR] Token: {token[:20]}...")
            print(f"[ERROR] Current time: {datetime.utcnow()}")
            flash('La conexión está tardando demasiado. Inténtalo de nuevo en unos minutos.', 'warning')
            return redirect(url_for('auth.login'))

        if not reset_token:
            print(f"[ERROR] Token no encontrado en BD: {token[:20]}...")
            print(f"[ERROR] Token length: {len(token)}")
            print(f"[ERROR] Token characters: {token[:10]}...{token[-10:]}")

            # Verificar si existe pero está usado (consulta optimizada)
            used_token = PasswordResetToken.query.filter_by(token=token).first()
            if used_token:
                print(f"[WARNING] Token encontrado pero usado: {used_token.used}")
                print(f"[WARNING] Token details: ID={used_token.id}, Email={used_token.email}, Used={used_token.used}")
                print(f"[WARNING] Created: {used_token.created_at}, Expires: {used_token.expires_at}")
                if used_token.used:
                    print(f"[ERROR] Token ya fue utilizado - posible problema de concurrencia")
                    flash('Este enlace de restablecimiento ya ha sido utilizado.', 'danger')
                else:
                    print(f"[ERROR] Token encontrado pero no usado - posible problema de consulta")
                    flash('Error interno del sistema. Inténtalo de nuevo.', 'danger')
            else:
                print("[ERROR] Token no existe en la base de datos")
                # Verificar si hay tokens similares
                similar_tokens = PasswordResetToken.query.filter(
                    PasswordResetToken.token.like(f"{token[:10]}%")
                ).all()
                if similar_tokens:
                    print(f"[WARNING] Tokens similares encontrados: {len(similar_tokens)}")
                    for t in similar_tokens[:3]:  # Mostrar solo los primeros 3
                        print(f"[WARNING]   Similar token: {t.token[:20]}... (ID: {t.id})")

            flash('El enlace de restablecimiento no es válido o ha expirado.', 'danger')
            return redirect(url_for('auth.login'))

        print(f"[OK] Token encontrado - ID: {reset_token.id}, Email: {reset_token.email}, Used: {reset_token.used}")
        print(f"[TIME] Created: {reset_token.created_at}")
        print(f"[TIME] Expires: {reset_token.expires_at}")
        print(f"[TIME] Current: {datetime.utcnow()}")

        # Verificar expiración con más detalle
        is_expired = reset_token.is_expired()
        print(f"[SEARCH] Método is_expired(): {is_expired}")

        if is_expired:
            print(f"[ERROR] Token expirado")
            print(f"[ERROR] Token details: ID={reset_token.id}, Email={reset_token.email}")
            print(f"[ERROR] Created: {reset_token.created_at}, Expires: {reset_token.expires_at}")
            print(f"[ERROR] Current time: {datetime.utcnow()}")
            print(f"[ERROR] Time difference: {(datetime.utcnow() - reset_token.expires_at).total_seconds()} seconds")
            flash('El enlace de restablecimiento ha expirado. Solicita uno nuevo.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        total_time = time.time() - start_time
        print(f"[OK] Token válido, mostrando formulario (tiempo total: {total_time:.2f}s)")

    except Exception as db_error:
        error_time = time.time() - start_time
        print(f"[ERROR] ERROR de base de datos después de {error_time:.2f}s: {db_error}")
        print(f"[SEARCH] Tipo de error: {type(db_error).__name__}")

        # Intentar rollback si es necesario
        try:
            db.session.rollback()
        except:
            pass

        flash('Error interno del servidor. La conexión está tardando demasiado. Inténtalo de nuevo.', 'danger')
        return redirect(url_for('auth.login'))

    print(f"[OK] Token encontrado - ID: {reset_token.id}, Email: {reset_token.email}, Used: {reset_token.used}")
    print(f"[TIME] Created: {reset_token.created_at}")
    print(f"[TIME] Expires: {reset_token.expires_at}")
    print(f"[TIME] Current: {datetime.utcnow()}")

    # Verificar expiración con más detalle
    is_expired = reset_token.is_expired()
    print(f"[SEARCH] Método is_expired(): {is_expired}")

    if is_expired:
        print(f"[ERROR] Token expirado")
        print(f"   Expires at: {reset_token.expires_at}")
        print(f"   Current time: {datetime.utcnow()}")
        print(f"   Difference: {(datetime.utcnow() - reset_token.expires_at).total_seconds()} seconds")
        flash('El enlace de restablecimiento ha expirado. Solicita uno nuevo.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    print("[OK] Token válido, mostrando formulario")

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
        elif reset_token.user_type == 'coordinador':
            user = Coordinador.query.get(reset_token.user_id)
            password_field = 'password'
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
            print(f"[OK] Contraseña actualizada exitosamente para {reset_token.email}")

            flash('Tu contraseña ha sido restablecida exitosamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Error al restablecer contraseña: {e}")
            flash('Error al restablecer la contraseña. Inténtalo de nuevo.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

    return render_template('reset_password.html', token=token, now=datetime.now())
