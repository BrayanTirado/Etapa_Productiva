from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from app.models.users import Coordinador, Instructor, Aprendiz, TokenInstructor, TokenCoordinador, Programa, Notificacion, Sede, Administrador
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import secrets
from sqlalchemy import or_

bp = Blueprint('coordinador_bp', __name__, url_prefix='/coordinador')

# -------------------------------
# Decorador para proteger rutas de coordinador
# -------------------------------
def coordinador_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not hasattr(current_user, "id_coordinador"):
            flash("No tienes permisos para acceder a esta sección", "error")
            return redirect(url_for('coordinador_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------
# Función para enviar notificación
# -------------------------------
def enviar_notificacion(mensaje, destinatario_id=None, rol_destinatario=None):
    noti = Notificacion(
        mensaje=mensaje,
        remitente_id=current_user.id_coordinador,
        rol_remitente="Coordinador",
        destinatario_id=destinatario_id,
        rol_destinatario=rol_destinatario,
        visto=False
    )
    db.session.add(noti)
    db.session.commit()

# -------------------------------
# Función para obtener nombre del remitente
# -------------------------------
def obtener_remitente(noti):
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
            return f"{getattr(remitente, 'nombre', 'Administrador')} {getattr(remitente, 'apellido','')}".strip()
    return "Sistema"

# -------------------------------
# Registro inicial del coordinador
# -------------------------------
@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        token_input = request.form.get('token')
        token_obj = TokenCoordinador.query.filter_by(token=token_input, usado=False).first()
        if not token_obj:
            flash("Token inválido o ya usado", "error")
            return render_template('coordinador/registro.html', now=datetime.now())

        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        correo = request.form.get('correo')
        celular = request.form.get('celular')
        password = request.form.get('password')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular, password]):
            flash("Todos los campos son obligatorios", "error")
            return render_template('coordinador/registro.html', now=datetime.now())

        password_hash = generate_password_hash(password)
        coordinador = Coordinador(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            correo=correo,
            celular=celular,
            password=password_hash
        )

        try:
            db.session.add(coordinador)
            token_obj.usado = True
            db.session.commit()
            # ✅ Flash de éxito
            flash("Registro exitoso. Ahora inicia sesión", "success")
            return render_template('coordinador/registro.html', now=datetime.now())  # Mostrar modal en la misma página
        except Exception as e:
            db.session.rollback()
            flash(f"Ocurrió un error al registrar: {str(e)}", "error")
            return render_template('coordinador/registro.html', now=datetime.now())

    return render_template('coordinador/registro.html', now=datetime.now())


# -------------------------------
# Login del coordinador
# -------------------------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        documento = request.form.get('documento')
        password = request.form.get('password')

        coordinador = Coordinador.query.filter_by(documento=documento).first()
        if not coordinador or not check_password_hash(coordinador.password, password):
            flash("Documento o contraseña incorrectos", "error")
            return render_template('coordinador/login.html', now=datetime.now())

        login_user(coordinador)
        return redirect(url_for('coordinador_bp.dashboard'))

    return render_template('login.html', now=datetime.now())

# -------------------------------
# Logout del coordinador
# -------------------------------
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión", "success")
    return redirect(url_for('coordinador_bp.login'))

# -------------------------------
# Dashboard coordinador
# -------------------------------
@bp.route('/dashboard')
@login_required
@coordinador_required
def dashboard():
    sede_creada = current_user.sede
    notificaciones_no_leidas = Notificacion.query.filter_by(
        rol_destinatario='Coordinador',
        destinatario_id=current_user.id_coordinador,
        visto=False
    ).count() or 0
    administradores = Administrador.query.all()
    return render_template(
        'coordinador/dashboard_coordinador.html',
        sede_creada=sede_creada,
        notificaciones_no_leidas=notificaciones_no_leidas,
        roles=["Administrador", "Instructor", "Aprendiz"],
        administradores=administradores,
        now=datetime.now()
    )

@bp.route('/dashboard/instructores')
@login_required
@coordinador_required
def dashboard_instructores():
    instructores = Instructor.query.filter_by(coordinador_id=current_user.id_coordinador).all()
    return render_template(
        'coordinador/listar_instructores.html',
        instructores=instructores
    )


@bp.route('/listar_instructores')
@login_required
@coordinador_required
def listar_instructores():
    # Traemos todos los instructores de la base de datos
    instructores = Instructor.query.all()
    return render_template('coordinador/listar_instructores.html', instructores=instructores)



# -------------------------------
# Generación de token para instructores
# -------------------------------
@bp.route('/generar_token', methods=['GET', 'POST'])
@login_required
@coordinador_required
def generar_token():
    if request.method == 'POST':
        dias_validos = int(request.form.get('dias', 7))
        token_str = secrets.token_urlsafe(8)
        fecha_expiracion = datetime.utcnow() + timedelta(days=dias_validos)

        token = TokenInstructor(
            token=token_str,
            fecha_expiracion=fecha_expiracion,
            coordinador_id=current_user.id_coordinador
        )
        db.session.add(token)
        db.session.commit()
        flash(f"Token generado: {token_str} (válido {dias_validos} días)", "success")

        enviar_notificacion(
            mensaje=f"Se ha generado un nuevo token para instructores: {token_str}",
            rol_destinatario="Instructor"
        )

        return redirect(url_for('coordinador_bp.dashboard'))

    return render_template('coordinador/generar_token.html', now=datetime.now())

# -------------------------------
# Asignar aprendices a instructores
# -------------------------------
@bp.route('/asignar_aprendiz', methods=['GET', 'POST'])
@login_required
@coordinador_required
def asignar_aprendiz():
    instructores = Instructor.query.all()
    aprendices = []
    aprendices_asignados = []
    programa = None
    ficha = request.args.get("ficha")

    if ficha:
        programa = Programa.query.filter_by(ficha=ficha).first()
        if programa:
            # Aprendices disponibles (sin asignar)
            aprendices = Aprendiz.query.filter_by(
                programa_id=programa.id_programa,
                instructor_id=None
            ).all()

            # Aprendices ya asignados en esa ficha
            aprendices_asignados = Aprendiz.query.filter(
                Aprendiz.programa_id == programa.id_programa,
                Aprendiz.instructor_id.isnot(None)
            ).all()
    else:
        aprendices = Aprendiz.query.filter_by(instructor_id=None).all()
        aprendices_asignados = Aprendiz.query.filter(Aprendiz.instructor_id.isnot(None)).all()

    if request.method == "POST":
        aprendiz_ids = request.form.getlist("aprendices")
        instructor_id = request.form.get("instructor_id")

        if not aprendiz_ids or not instructor_id:
            flash("Debes seleccionar al menos un aprendiz y un instructor", "warning")
            return redirect(url_for("coordinador_bp.asignar_aprendiz", ficha=ficha))

        for aprendiz_id in aprendiz_ids:
            aprendiz = Aprendiz.query.get(int(aprendiz_id))
            if aprendiz:
                aprendiz.instructor_id = int(instructor_id)
                db.session.add(aprendiz)

                enviar_notificacion(
                    mensaje=f"Se te ha asignado un nuevo aprendiz: {aprendiz.nombre} {aprendiz.apellido}",
                    destinatario_id=instructor_id,
                    rol_destinatario="Instructor"
                )

        db.session.commit()
        flash("Aprendices asignados correctamente", "success")
        return redirect(url_for("coordinador_bp.asignar_aprendiz", ficha=ficha))

    programas = Programa.query.group_by(Programa.ficha).all()

    return render_template(
        "coordinador/asignar_aprendiz.html",
        programas=programas,
        aprendices=aprendices,
        aprendices_asignados=aprendices_asignados,
        instructores=instructores,
        programa=programa,
        now=datetime.now()
    )


# -------------------------------
# Enviar mensaje a un rol o usuario específico
# -------------------------------
@bp.route('/enviar_mensaje', methods=['POST'])
@login_required
@coordinador_required
def enviar_mensaje():
    rol_destinatario = request.form.get('rol_destinatario')
    destinatario_id = request.form.get('destinatario_id')
    motivo = request.form.get('motivo')
    mensaje = request.form.get('mensaje')

    if not rol_destinatario:
        flash("Debes seleccionar un rol para enviar el mensaje.", "danger")
        return redirect(url_for('coordinador_bp.dashboard'))

    destinatario_id = int(destinatario_id) if destinatario_id else None

    enviar_notificacion(
        mensaje=f"[{motivo}] {mensaje}",
        destinatario_id=destinatario_id,
        rol_destinatario=rol_destinatario
    )
    flash("Notificación enviada correctamente.", "success")
    return redirect(url_for('coordinador_bp.dashboard'))


# -------------------------------
# Función para obtener nombre del remitente (corregida)
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
        # Intentamos traer el nombre completo del administrador (si existe)
        remitente = Administrador.query.filter_by(id_admin=noti.remitente_id).first()
        if remitente:
            # ajusta los atributos si tu modelo administrador usa otros nombres
            return f"{getattr(remitente, 'nombre', 'Administrador')} {getattr(remitente, 'apellido', '')}".strip()

    # Si no hay remitente encontrado o rol desconocido -> "Sistema"
    return "Sistema"


# -------------------------------
# Listar notificaciones del coordinador (sin cambios funcionales, usamos obtener_remitente corregida)
# -------------------------------
@bp.route('/notificaciones')
@login_required
@coordinador_required
def notificaciones():
    # Página actual desde la query string
    pagina = request.args.get('pagina', 1, type=int)
    per_page = 10  # Notificaciones por página

    # Query filtrando por coordinador
    pagination = Notificacion.query.filter(
        Notificacion.rol_destinatario == "Coordinador",
        or_(Notificacion.destinatario_id == current_user.id_coordinador, Notificacion.destinatario_id == None)
    ).order_by(Notificacion.fecha_creacion.desc()).paginate(page=pagina, per_page=per_page, error_out=False)

    notificaciones = pagination.items
    total_paginas = pagination.pages

    # Asignar nombre legible del remitente
    for noti in notificaciones:
        noti.remitente_nombre = obtener_remitente(noti)

    return render_template(
        'notificacion/listar.html',
        notificaciones=notificaciones,
        pagina_actual=pagina,
        total_paginas=total_paginas,
        now=datetime.now()
    )

# -------------------------------
# Marcar notificación como vista y ver detalle
# -------------------------------
@bp.route('/notificacion/<int:noti_id>')
@login_required
def ver_notificacion(noti_id):
    noti = Notificacion.query.get_or_404(noti_id)

    # marcar vista
    noti.visto = True
    db.session.commit()

    # obtener nombre legible (sin prefijo)
    remitente_nombre = obtener_remitente(noti)
    
    fecha_local = noti.fecha_creacion - timedelta(hours=5)  # Ajuste a GMT-5 (Colombia)


    return render_template(
        'notificacion/ver_notificacion.html',
        notificacion=noti,
        remitente_nombre=remitente_nombre,
        now=datetime.now(),
        fecha_local=fecha_local
    )
    
#Responder notificacion
# Responder notificación
@bp.route('/notificacion/<int:noti_id>/responder', methods=['GET', 'POST'])
@login_required
def responder_notificacion(noti_id):
    noti = Notificacion.query.get_or_404(noti_id)

    if request.method == 'POST':
        respuesta = request.form.get('respuesta')

        # Detectar ID del usuario según su rol
        if current_user.__class__.__name__ == "Administrador":
            remitente_id = current_user.id_adm
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
            flash('Respuesta enviada con éxito.', 'success')
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

    return redirect(url_for('index'))

@bp.route('/notificaciones/marcar_todas', methods=['POST'])
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
# Crear sede
# -------------------------------
@bp.route('/crear_sede', methods=['GET', 'POST'])
@login_required
@coordinador_required
def crear_sede():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        ciudad = request.form.get('ciudad')
        token_input = request.form.get('token')

        if not all([nombre, ciudad, token_input]):
            flash("Token, nombre y ciudad son obligatorios", "error")
            return render_template('crear_sede.html', now=datetime.now())

        # Validar token
        token_obj = TokenCoordinador.query.filter_by(token=token_input).first()
        if not token_obj:
            flash("Token inválido", "error")
            return render_template('crear_sede.html', now=datetime.now())

        # Verificar que ya fue usado por el coordinador
        if not token_obj.usado:
            flash("El token aún no ha sido usado para registrar el coordinador", "error")
            return render_template('crear_sede.html', now=datetime.now())

        # Verificar si ya fue usado para crear una sede
        if getattr(token_obj, 'usado_para_sede', False):
            flash("Este token ya se ha usado para registrar una sede", "error")
            return render_template('crear_sede.html', now=datetime.now())

        # Crear sede
        sede = Sede(
            nombre=nombre,
            ciudad=ciudad
        )

        try:
            db.session.add(sede)
            db.session.flush()  # Flush para generar el ID de la sede antes de asignar

            # Asignar la sede al coordinador actual
            current_user.sede_id = sede.id_sede  # O alternativamente: current_user.sede = sede
            # Si usas la relación: sede.coordinadores.append(current_user)

            # Marcar token como usado para sede
            token_obj.usado_para_sede = True
            db.session.commit()

            # Flash de éxito
            flash(f"Sede '{sede.nombre}' en '{sede.ciudad}' creada exitosamente. Coordinador asignado automáticamente.", "success_sede")
            return redirect(url_for('coordinador_bp.crear_sede'))  # redirige a mismo form
        except Exception as e:
            db.session.rollback()
            flash(f"Ocurrió un error al registrar la sede: {str(e)}", "error")
            return render_template('crear_sede.html', now=datetime.now())

    return render_template('crear_sede.html', now=datetime.now())
