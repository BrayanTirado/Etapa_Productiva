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
    try:
        msg = Message(
            subject='Recuperación de contraseña - SENA',
            recipients=[email],
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
        print(f"Email de recuperación enviado a {email}")
    except Exception as e:
        print(f"Error al enviar email: {e}")
        raise

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

        print(f"🔑 Generando token para {email} (tipo: {user_type})")
        print(f"⏰ Token expira: {expires_at}")

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

        print(f"👤 User ID: {user_id} (atributo: {id_attr})")

        reset_token = PasswordResetToken(
            token=token,
            email=email,
            user_type=user_type,
            user_id=user_id,
            expires_at=expires_at
        )

        try:
            print(f"💾 Guardando token en BD...")

            # Verificar que la tabla existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'password_reset_token' not in tables:
                print(f"❌ ERROR: Tabla 'password_reset_token' no existe")
                print(f"📋 Tablas disponibles: {tables}")
                db.create_all()
                print(f"🔧 Tablas creadas")

            db.session.add(reset_token)
            db.session.commit()
            print(f"✅ Token guardado exitosamente - ID: {reset_token.id}")

            # Verificar que se guardó correctamente
            saved_token = PasswordResetToken.query.filter_by(token=token).first()
            if saved_token:
                print(f"🔍 Verificación: Token encontrado en BD - ID: {saved_token.id}")
                print(f"   Token: {saved_token.token}")
                print(f"   Email: {saved_token.email}")
                print(f"   Expires: {saved_token.expires_at}")
            else:
                print(f"❌ ERROR: Token no se encontró después del commit")

            # Generar URL de restablecimiento
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            print(f"🔗 URL generada: {reset_url}")

            # Enviar email (simulado)
            send_reset_email(email, reset_url)

            flash('Si tu correo electrónico está registrado, recibirás un enlace para restablecer tu contraseña.', 'info')
            return redirect(url_for('auth.login'))

        except Exception as e:
            print(f"❌ ERROR al guardar token: {e}")
            print(f"🔍 Tipo de error: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            db.session.rollback()
            flash('Error al procesar la solicitud. Inténtalo de nuevo.', 'danger')
            return redirect(url_for('auth.forgot_password'))

    return render_template('forgot_password.html', now=datetime.now())


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Página para restablecer contraseña usando token"""
    print(f"🔍 Validando token: {token[:20]}...")
    print(f"📏 Longitud del token: {len(token)}")

    # Validar que el token no esté vacío
    if not token or len(token.strip()) == 0:
        print("❌ Token vacío o inválido")
        flash('El enlace de restablecimiento no es válido o ha expirado.', 'danger')
        return redirect(url_for('auth.login'))

    # Verificar conexión a BD y tabla
    try:
        # Verificar que podemos hacer consultas
        total_tokens = PasswordResetToken.query.count()
        print(f"📊 Total de tokens en BD: {total_tokens}")

        # Buscar token válido
        reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()

        if not reset_token:
            print(f"❌ Token no encontrado en BD: {token[:20]}...")
            # Verificar si existe pero está usado
            used_token = PasswordResetToken.query.filter_by(token=token).first()
            if used_token:
                print(f"⚠️ Token encontrado pero usado: {used_token.used}")
                print(f"   Token data: ID={used_token.id}, Email={used_token.email}")
            else:
                print("❌ Token no existe en la base de datos")
                # Mostrar algunos tokens existentes para debug
                all_tokens = PasswordResetToken.query.limit(3).all()
                if all_tokens:
                    print("🔍 Tokens existentes en BD:")
                    for t in all_tokens:
                        print(f"   - {t.token[:20]}... (Email: {t.email})")
                else:
                    print("🔍 No hay tokens en la BD")

            flash('El enlace de restablecimiento no es válido o ha expirado.', 'danger')
            return redirect(url_for('auth.login'))

    except Exception as db_error:
        print(f"❌ ERROR de base de datos: {db_error}")
        flash('Error interno del servidor. Inténtalo de nuevo.', 'danger')
        return redirect(url_for('auth.login'))

    print(f"✅ Token encontrado - ID: {reset_token.id}, Email: {reset_token.email}, Used: {reset_token.used}")
    print(f"⏰ Created: {reset_token.created_at}")
    print(f"⏰ Expires: {reset_token.expires_at}")
    print(f"⏰ Current: {datetime.utcnow()}")

    # Verificar expiración con más detalle
    is_expired = reset_token.is_expired()
    print(f"🔍 Método is_expired(): {is_expired}")

    if is_expired:
        print(f"❌ Token expirado")
        print(f"   Expires at: {reset_token.expires_at}")
        print(f"   Current time: {datetime.utcnow()}")
        print(f"   Difference: {(datetime.utcnow() - reset_token.expires_at).total_seconds()} seconds")
        flash('El enlace de restablecimiento ha expirado. Solicita uno nuevo.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    print("✅ Token válido, mostrando formulario")

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
