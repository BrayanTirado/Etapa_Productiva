from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models.users import Administrador, TokenCoordinador, Notificacion, Aprendiz, Coordinador, Instructor
from app import db
import secrets
from datetime import datetime, timedelta
from functools import wraps

adm_bp = Blueprint('adm_bp', __name__, url_prefix='/adm')

# -------------------------------
# Decorador para proteger rutas de administrador
# -------------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Administrador):
            flash("No tienes permisos para acceder a esta sección", "error")
            return redirect(url_for('adm_login'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------
# Función para generar token aleatorio
# -------------------------------
def generate_random_token(length=8):
    return secrets.token_urlsafe(length)

# -------------------------------
# Función para enviar notificación
# -------------------------------
def enviar_notificacion(mensaje, destinatario_id=None, rol_destinatario=None):
    # Determinar remitente dinámicamente según rol
    if current_user.rol_user == "administrador":
        remitente_id = current_user.id_admin
    elif current_user.rol_user == "coordinador":
        remitente_id = current_user.id_coordinador
    elif current_user.rol_user == "instructor":
        remitente_id = current_user.id_instructor
    elif current_user.rol_user == "aprendiz":
        remitente_id = current_user.id_aprendiz
    else:
        return False  # rol no válido

    noti = Notificacion(
        mensaje=mensaje,
        remitente_id=remitente_id,
        rol_remitente=current_user.rol_user.capitalize(),
        destinatario_id=destinatario_id,
        rol_destinatario=rol_destinatario,
        visto=False
    )
    db.session.add(noti)
    db.session.commit()
    return True


# -------------------------------
# Login administrador
# -------------------------------
@adm_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and isinstance(current_user, Administrador):
        return redirect(url_for('adm_bp.dashboard'))

    if request.method == 'POST':
        documento = request.form.get('documento')
        password = request.form.get('password')
        admin = Administrador.query.filter_by(documento=documento).first()
        if not admin or not check_password_hash(admin.password, password):
            flash("Documento o contraseña incorrectos", "error")
            return render_template('login.html')
        login_user(admin)
        flash("Inicio de sesión exitoso", "success")
        return redirect(url_for('adm_bp.dashboard'))

    return render_template('login.html')

# -------------------------------
# Dashboard administrador
# -------------------------------
@adm_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    tokens = TokenCoordinador.query.filter_by(admin_id=current_user.id_admin).all()
    notificaciones_no_leidas = Notificacion.query.filter_by(
        rol_destinatario="Administrador",
        visto=False
    ).count()

    aprendices = Aprendiz.query.all()
    coordinadores = Coordinador.query.all()
    instructores = Instructor.query.all()

    return render_template(
        'adm/dashboard_adm.html',
        tokens=tokens,
        notificaciones_no_leidas=notificaciones_no_leidas,
        now=datetime.now(),
        aprendices=aprendices,
        coordinadores=coordinadores,
        instructores=instructores,
        admin_nombre=f"{current_user.nombre} {current_user.apellido}",  # [POINTING] agregado para saludo
    )

# -------------------------------
# Generar token para coordinador
# -------------------------------
@adm_bp.route('/generar_token', methods=['POST'])
@login_required
@admin_required
def generar_token():
    dias_validos = int(request.form.get('dias', 7))
    token_str = generate_random_token(8)
    fecha_expiracion = datetime.utcnow() + timedelta(days=dias_validos)
    token = TokenCoordinador(
        token=token_str,
        admin_id=current_user.id_admin,
        fecha_expiracion=fecha_expiracion,
        usado=False
    )
    db.session.add(token)
    db.session.commit()

    # Enviar notificación al rol coordinador (si quieres notificarlo)
    enviar_notificacion(
        mensaje=f"Se ha generado un nuevo token para coordinadores: {token_str}",
        rol_destinatario="Coordinador"
    )

    flash(f"Token generado: {token_str} (válido {dias_validos} días)", "success")
    return redirect(url_for('adm_bp.dashboard'))

# -------------------------------
# Eliminar token
# -------------------------------
@adm_bp.route('/eliminar_token/<int:token_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_token(token_id):
    token = TokenCoordinador.query.get_or_404(token_id)
    try:
        db.session.delete(token)
        db.session.commit()
        flash("Token eliminado correctamente", "success")
    except Exception:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception("Error eliminando token")
        flash("Error eliminando token", "error")
    return redirect(url_for('adm_bp.dashboard'))

# -------------------------------
# Enviar mensaje a un rol
# -------------------------------
@adm_bp.route('/enviar_mensaje', methods=['GET', 'POST'])
@login_required
@admin_required
def enviar_mensaje():
    roles_disponibles = ["Coordinador", "Instructor", "Aprendiz"]

    coordinadores = Coordinador.query.all()
    instructores = Instructor.query.all()
    aprendices = Aprendiz.query.all()

    notificaciones_no_leidas = Notificacion.query.filter_by(
        rol_destinatario="Administrador",
        visto=False
    ).count()

    if request.method == 'POST':
        rol_destinatario = request.form.get('rol_destinatario')
        destinatario_id = request.form.get('destinatario_id')  # puede venir vacío
        motivo = request.form.get('motivo')
        mensaje = request.form.get('mensaje')

        if not rol_destinatario:
            flash("Debes seleccionar un rol para enviar el mensaje.", "danger")
            return redirect(url_for('adm_bp.dashboard'))

        # [OK] Caso 1: mensaje a un usuario específico
        if destinatario_id:
            destinatario_id = int(destinatario_id)

            user = None
            if rol_destinatario == "Coordinador":
                user = Coordinador.query.get(destinatario_id)
            elif rol_destinatario == "Instructor":
                user = Instructor.query.get(destinatario_id)
            elif rol_destinatario == "Aprendiz":
                user = Aprendiz.query.get(destinatario_id)

            if user:
                # Determinar nombre completo según rol
                if rol_destinatario == "Instructor":
                    nombre_completo = f"{user.nombre_instructor} {user.apellido_instructor}"
                else:
                    nombre_completo = f"{user.nombre} {user.apellido}"

                enviar_notificacion(
                    mensaje=f"[{motivo}] {mensaje}",
                    destinatario_id=destinatario_id,
                    rol_destinatario=rol_destinatario
                )
                # [OK] Mensaje más descriptivo con nombre y rol
                flash(
                    f"Notificación enviada con éxito a {nombre_completo} ({rol_destinatario}).",
                    "success"
                )
            else:
                flash("El destinatario no existe o no pertenece a ese rol.", "danger")

        # [OK] Caso 2: mensaje general al rol completo
        else:
            enviar_notificacion(
                mensaje=f"[{motivo}] {mensaje}",
                destinatario_id=None,  # [POINTING] general
                rol_destinatario=rol_destinatario
            )
            flash(f"Notificación general enviada a todos los {rol_destinatario.lower()}s.", "success")

        return redirect(url_for('adm_bp.dashboard'))

    return render_template(
        'adm/dashboard_adm.html',
        roles=roles_disponibles,
        coordinadores=coordinadores,
        instructores=instructores,
        aprendices=aprendices,
        notificaciones_no_leidas=notificaciones_no_leidas,
        now=datetime.now(),
        admin_nombre=f"{current_user.nombre} {current_user.apellido}"
    )

# -------------------------------
# Listar notificaciones
# -------------------------------
@adm_bp.route('/notificaciones')
@login_required
@admin_required
def notificaciones():
    # Obtener la página desde la query string, por defecto 1
    pagina = request.args.get('pagina', 1, type=int)
    per_page = 10  # Notificaciones por página

    # Query con paginación
    from sqlalchemy import or_
    pagination = Notificacion.query.filter(
        Notificacion.rol_destinatario == "Administrador",
        or_(Notificacion.destinatario_id == current_user.id_admin, Notificacion.destinatario_id == None)
    ).order_by(Notificacion.fecha_creacion.desc()).paginate(page=pagina, per_page=per_page, error_out=False)

    notificaciones = pagination.items
    total_paginas = pagination.pages

    return render_template(
        'notificacion/listar.html',
        notificaciones=notificaciones,
        pagina_actual=pagina,
        total_paginas=total_paginas,
        now=datetime.now()
    )

# -------------------------------
# Función para obtener nombre del remitente
# -------------------------------
def obtener_remitente(noti):
    """
    Devuelve el nombre simple del remitente (sin prefijos como 'De: ').
    Si no se encuentra el remitente, devuelve 'Sistema'.
    """
    role = (noti.rol_remitente or "").strip()

    if role == "Coordinador":
        remitente = Coordinador.query.filter_by(id_coordinador=noti.remitente_id).first()
        if remitente:
            return f"{remitente.nombre} {remitente.apellido}"
    elif role == "Instructor":
        remitente = Instructor.query.filter_by(id_instructor=noti.remitente_id).first()
        if remitente:
            return f"{remitente.nombre_instructor} {remitente.apellido_instructor}"
    elif role == "Aprendiz":
        remitente = Aprendiz.query.filter_by(id_aprendiz=noti.remitente_id).first()
        if remitente:
            return f"{remitente.nombre} {remitente.apellido}"
    elif role == "Administrador":
        remitente = Administrador.query.filter_by(id_admin=noti.remitente_id).first()
        if remitente:
            return f"{getattr(remitente, 'nombre', 'Administrador')} {getattr(remitente, 'apellido', '')}".strip()

    # Si no hay remitente encontrado o rol desconocido -> "Sistema"
    return "Sistema"

# -------------------------------
# Marcar notificación como vista
# -------------------------------
@adm_bp.route('/notificacion/ver/<int:noti_id>')
@login_required
@admin_required
def ver_notificacion(noti_id):
    noti = Notificacion.query.get_or_404(noti_id)
    noti.visto = True
    db.session.commit()
    fecha_local = noti.fecha_creacion - timedelta(hours=5)  # Ajuste a GMT-5 (Colombia)

    # Obtener nombre del remitente
    remitente_nombre = obtener_remitente(noti)

    return render_template('notificacion/ver_notificacion.html', notificacion=noti, remitente_nombre=remitente_nombre, now=datetime.now(), fecha_local=fecha_local)



# Responder notificación (Administrador)
@adm_bp.route('/notificacion/<int:noti_id>/responder', methods=['GET', 'POST'])
@login_required
def responder_notificacion(noti_id):
    noti = Notificacion.query.get_or_404(noti_id)

    if request.method == 'POST':
        respuesta = request.form.get('respuesta')

        # Detectar ID del usuario según su rol
        if current_user.__class__.__name__ == "Administrador":
            remitente_id = current_user.id_admin
        elif current_user.__class__.__name__ == "Coordinador":
            remitente_id = current_user.id_coordinador
        elif current_user.__class__.__name__ == "Instructor":
            remitente_id = current_user.id_instructor
        elif current_user.__class__.__name__ == "Aprendiz":
            remitente_id = current_user.id_aprendiz
        else:
            remitente_id = None  # fallback

        if respuesta and remitente_id:
            nueva = Notificacion(
                mensaje=f"[Respuesta a '{noti.mensaje.split(']')[0].replace('[','')}'] {respuesta}",
                remitente_id=remitente_id,
                rol_remitente=current_user.__class__.__name__,
                destinatario_id=noti.remitente_id,
                rol_destinatario=noti.rol_remitente
            )
            db.session.add(nueva)
            db.session.commit()
        else:
            flash('No se pudo enviar la respuesta. Asegúrate de escribir un mensaje.', 'danger')

    # Redirigir según el rol
    if current_user.__class__.__name__ == "Administrador":
        return redirect(url_for('adm_bp.notificaciones'))
    elif current_user.__class__.__name__ == "Coordinador":
        return redirect(url_for('coordinador_bp.notificaciones'))
    elif current_user.__class__.__name__ == "Instructor":
        return redirect(url_for('instructor_bp.notificaciones'))
    elif current_user.__class__.__name__ == "Aprendiz":
        return redirect(url_for('aprendiz_bp.notificaciones'))

    return redirect(url_for('adm_bp.notificaciones'))  # fallback

@adm_bp.route('/notificaciones/marcar_todas', methods=['POST'])
@login_required
def marcar_todas_notificaciones():

    # Detecta el id del usuario según rol
    if current_user.__class__.__name__ == "Administrador":
        user_id = current_user.id_admin
        rol = "Administrador"
    elif current_user.__class__.__name__ == "Coordinador":
        user_id = current_user.id_coordinador
        rol = "Coordinador"
    elif current_user.__class__.__name__ == "Instructor":
        user_id = current_user.id_instructor
        rol = "Instructor"
    elif current_user.__class__.__name__ == "Aprendiz":
        user_id = current_user.id_aprendiz
        rol = "Aprendiz"
    else:
        return "", 400

    # Marcar todas como vistas
    Notificacion.query.filter_by(destinatario_id=user_id, rol_destinatario=rol, visto=False).update({"visto": True})
    db.session.commit()
    return "", 200



# -------------------------------
# Editar perfil administrador
# -------------------------------
@adm_bp.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_perfil():
    if request.method == 'POST':
        nombre = request.form.get('nombre').strip()
        apellido = request.form.get('apellido').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo').strip().lower()
        celular = request.form.get('celular').strip()
        password = request.form.get('password')

        if not all([nombre, apellido, documento, correo, celular]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('adm_bp.editar_perfil'))

        # Verificar si documento o correo ya existen en otro admin
        existing_admin = Administrador.query.filter(
            (Administrador.documento == documento) | (Administrador.correo == correo)
        ).filter(Administrador.id_admin != current_user.id_admin).first()

        if existing_admin:
            flash('Documento o correo ya están en uso por otro administrador.', 'danger')
            return redirect(url_for('adm_bp.editar_perfil'))

        # Actualizar datos
        current_user.nombre = nombre
        current_user.apellido = apellido
        current_user.documento = documento
        current_user.correo = correo
        current_user.celular = celular

        if password:
            from werkzeug.security import generate_password_hash
            current_user.password = generate_password_hash(password)

        try:
            db.session.commit()
            flash('Perfil actualizado correctamente.', 'success')
            return redirect(url_for('adm_bp.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar perfil: {str(e)}', 'danger')

    return render_template('adm/editar_perfil.html', admin=current_user, now=datetime.now())

# -------------------------------
# Logout administrador
# -------------------------------
@adm_bp.route('/logout')
@login_required
@admin_required
def logout():
    logout_user()
    flash("Has cerrado sesión", "success")
    return redirect(url_for('auth.login'))
