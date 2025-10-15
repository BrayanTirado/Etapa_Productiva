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

        # --- Obtener sede desde el token si el token la contiene ---
        # soporta token_obj.sede_id o token_obj.id_sede (según cómo definiste la columna)
        sede_from_token = getattr(token_obj, 'sede_id', None) or getattr(token_obj, 'id_sede', None)

        # Si no quieres asignar sede automáticamente (coordinador la crea luego),
        # deja sede_from_token = None. Aquí lo usamos solo si existe.
        coordinador = Coordinador(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            correo=correo,
            celular=celular,
            password=password_hash,
            sede_id=sede_from_token  # será None si el token no tiene sede
        )

        try:
            db.session.add(coordinador)
            token_obj.usado = True
            db.session.commit()

            # Notificación a administradores
            noti = Notificacion(
                motivo="Se ha registrado un nuevo Coordinador",
                mensaje=f"{coordinador.nombre} {coordinador.apellido}",
                remitente_id=coordinador.id_coordinador,
                rol_remitente="Coordinador",
                destinatario_id=None,
                rol_destinatario="Administrador",
                visto=False
            )
            db.session.add(noti)
            db.session.commit()

            flash("Registro exitoso. Ahora inicia sesión", "success")
            return render_template('coordinador/registro.html', now=datetime.now())
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
    sede_creada = getattr(current_user, 'sede', None)

    notificaciones_no_leidas = Notificacion.query.filter_by(
        rol_destinatario="Coordinador",
        destinatario_id=current_user.id_coordinador,
        visto=False
    ).count() or 0

    tokens = TokenInstructor.query.filter_by(coordinador_id=current_user.id_coordinador).all()

    # Obtener filtro de sede
    sede_filter = request.args.get('sede_filter')

    # [OK] Filtrar instructores y aprendices por sede del coordinador o por filtro
    instructores = []
    aprendices = []
    if sede_filter:
        # Filtrar por sede seleccionada
        instructores = Instructor.query.filter_by(sede_id=int(sede_filter)).all()
        aprendices = Aprendiz.query.filter_by(sede_id=int(sede_filter)).all()
    elif sede_creada:
        # Filtrar por sede del coordinador
        instructores = Instructor.query.filter_by(sede_id=sede_creada.id_sede).all()
        aprendices = Aprendiz.query.filter_by(sede_id=sede_creada.id_sede).all()

    # [OK] Administradores siempre van completos
    administradores = Administrador.query.all()

    # Obtener todas las sedes para el filtro
    from app.models.users import Sede
    sedes = Sede.query.all()

    return render_template(
        'coordinador/dashboard_coordinador.html',
        sede_creada=sede_creada,
        notificaciones_no_leidas=notificaciones_no_leidas,
        roles=["Administrador", "Instructor", "Aprendiz"],
        tokens=tokens,
        now=datetime.now(),
        instructores=instructores,
        aprendices=aprendices,
        administradores=administradores,
        sedes=sedes
    )




@bp.route('/listar_instructores')
@login_required
@coordinador_required
def listar_instructores():
    instructores = Instructor.query.filter_by(sede_id=current_user.sede_id).all()
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

        # [OK] Verificar que el coordinador tenga una sede asignada
        if not current_user.sede_id:
            flash("Error: Debes crear una sede primero antes de generar tokens para instructores.", "error")
            return redirect(url_for('coordinador_bp.dashboard'))

        # [OK] Incluir la sede_id del coordinador al generar el token
        token = TokenInstructor(
            token=token_str,
            fecha_expiracion=fecha_expiracion,
            coordinador_id=current_user.id_coordinador,
            sede_id=current_user.sede_id   # [KEY] hereda la sede del coordinador
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
    # Solo instructores de la misma sede
    instructores = Instructor.query.filter_by(sede_id=current_user.sede_id).all()
    aprendices = []
    aprendices_asignados = []
    programa = None
    ficha = request.args.get("ficha")

    if ficha:
        programa = Programa.query.filter(Programa.ficha == ficha).first()
        if programa:
            # Aprendices disponibles (sin asignar) de la misma sede o sin sede
            aprendices = Aprendiz.query.filter(
                Aprendiz.programa_id == programa.id_programa,
                Aprendiz.instructor_id == None,
                or_(Aprendiz.sede_id == current_user.sede_id, Aprendiz.sede_id == None)
            ).all()

            # Aprendices ya asignados en esa ficha y sede
            aprendices_asignados = Aprendiz.query.filter(
                Aprendiz.programa_id == programa.id_programa,
                Aprendiz.instructor_id.isnot(None),
                Aprendiz.sede_id == current_user.sede_id
            ).all()

            # Debug: mostrar información
            print(f"DEBUG: Programa encontrado: {programa.nombre_programa}, Ficha: {programa.ficha}")
            print(f"DEBUG: Aprendices encontrados: {len(aprendices)}")
            for ap in aprendices:
                print(f"DEBUG: Aprendiz: {ap.nombre} {ap.apellido}, Programa ID: {ap.programa_id}, Instructor ID: {ap.instructor_id}")
        else:
            # Si no se encuentra el programa, resetear variables
            aprendices = []
            aprendices_asignados = []
            programa = None
            print(f"DEBUG: No se encontró programa para ficha {ficha}")
            flash(f"No se encontró un programa para la ficha {ficha}", "warning")
    else:
        # Sin ficha: mostrar todos los aprendices sin asignar de la sede o sin sede
        aprendices = Aprendiz.query.filter(
            Aprendiz.instructor_id == None,
            or_(Aprendiz.sede_id == current_user.sede_id, Aprendiz.sede_id == None)
        ).all()

        aprendices_asignados = Aprendiz.query.filter(
            Aprendiz.instructor_id.isnot(None),
            Aprendiz.sede_id == current_user.sede_id
        ).all()

    # ------------------------------
    # Procesar asignación (POST)
    # ------------------------------
    if request.method == "POST":
        aprendiz_ids = request.form.getlist("aprendices")
        instructor_id = request.form.get("instructor_id")

        if not aprendiz_ids or not instructor_id:
            flash("Debes seleccionar al menos un aprendiz y un instructor", "warning")
            return redirect(url_for("coordinador_bp.asignar_aprendiz", ficha=ficha))

        instructor = Instructor.query.get(int(instructor_id))
        if not instructor or instructor.sede_id != current_user.sede_id:
            flash("El instructor seleccionado no existe o no pertenece a tu sede", "error")
            return redirect(url_for("coordinador_bp.asignar_aprendiz", ficha=ficha))

        for aprendiz_id in aprendiz_ids:
            aprendiz = Aprendiz.query.get(int(aprendiz_id))
            if aprendiz:
                # Al asignar, se asegura que el aprendiz quede con la sede del instructor
                aprendiz.instructor_id = instructor.id_instructor
                aprendiz.coordinador_id = instructor.coordinador_id
                aprendiz.sede_id = instructor.sede_id  

                db.session.add(aprendiz)

                # Notificación al instructor
                from app.models.users import Notificacion
                noti = Notificacion(
                    motivo="Se te ha asignado un nuevo aprendiz",
                    mensaje=f"{aprendiz.nombre} {aprendiz.apellido}",
                    remitente_id=current_user.id_coordinador,
                    rol_remitente="Coordinador",
                    destinatario_id=instructor.id_instructor,
                    rol_destinatario="Instructor",
                    visto=False
                )
                db.session.add(noti)

        db.session.commit()
        flash("Aprendices asignados correctamente", "success")
        return redirect(url_for("coordinador_bp.asignar_aprendiz", ficha=ficha))

    # ------------------------------
    # Renderizar formulario (GET)
    # ------------------------------
    programas = (
        Programa.query
        .join(Aprendiz, Programa.id_programa == Aprendiz.programa_id)
        .filter(
            Aprendiz.instructor_id == None,
            or_(Aprendiz.sede_id == current_user.sede_id, Aprendiz.sede_id == None)
        )
        .group_by(Programa.id_programa)
        .all()
    )

    return render_template(
        "coordinador/asignar_aprendiz.html",
        programas=programas,
        aprendices=aprendices,
        aprendices_asignados=aprendices_asignados,
        instructores=instructores,
        programa=programa,
        now=datetime.now()
    )



@bp.route('/enviar_mensaje', methods=['GET', 'POST'])
@login_required
@coordinador_required
def enviar_mensaje():
    roles_disponibles = ["Administrador", "Instructor", "Aprendiz"]

    # ✅ Filtrar instructores y aprendices por sede del coordinador
    sede_id = current_user.sede_id
    administradores = Administrador.query.all()
    instructores = Instructor.query.filter_by(sede_id=sede_id).all()
    aprendices = Aprendiz.query.filter_by(sede_id=sede_id).all()

    notificaciones_no_leidas = Notificacion.query.filter_by(
        rol_destinatario="Coordinador",
        destinatario_id=current_user.id_coordinador,
        visto=False
    ).count()

    if request.method == 'POST':
        rol_destinatario = request.form.get('rol_destinatario')
        destinatario_id = request.form.get('destinatario_id')  # puede venir vacío
        motivo = request.form.get('motivo')
        mensaje = request.form.get('mensaje')

        if not rol_destinatario:
            flash("Debes seleccionar un rol para enviar el mensaje.", "danger")
            return redirect(url_for('coordinador_bp.dashboard'))

        # [OK] Caso 1: mensaje a un usuario específico
        if destinatario_id:
            destinatario_id = int(destinatario_id)

            user = None
            if rol_destinatario == "Administrador":
                user = Administrador.query.get(destinatario_id)
            elif rol_destinatario == "Instructor":
                user = Instructor.query.filter_by(id_instructor=destinatario_id, sede_id=sede_id).first()
            elif rol_destinatario == "Aprendiz":
                user = Aprendiz.query.filter_by(id_aprendiz=destinatario_id, sede_id=sede_id).first()

            if user:
                # Determinar nombre completo según rol
                if rol_destinatario == "Instructor":
                    nombre_completo = f"{user.nombre_instructor} {user.apellido_instructor}"
                elif rol_destinatario == "Administrador":
                    nombre_completo = f"{user.nombre} {user.apellido}"
                else:  # Aprendiz
                    nombre_completo = f"{user.nombre} {user.apellido}"

                enviar_notificacion(
                    mensaje=f"[{motivo}] {mensaje}",
                    destinatario_id=destinatario_id,
                    rol_destinatario=rol_destinatario
                )
                flash(
                    f"Notificación enviada con éxito a {nombre_completo} ({rol_destinatario}).",
                    "success"
                )
            else:
                flash("El destinatario no existe o no pertenece a tu sede.", "danger")

        # [OK] Caso 2: mensaje general al rol completo
        else:
            enviar_notificacion(
                mensaje=f"[{motivo}] {mensaje}",
                destinatario_id=None,  # [POINTING] general
                rol_destinatario=rol_destinatario
            )
            flash(f"Notificación general enviada a todos los {rol_destinatario.lower()}s.", "success")

        return redirect(url_for('coordinador_bp.dashboard'))

    return render_template(
        'coordinador/dashboard.html',
        roles=roles_disponibles,
        administradores=administradores,
        instructores=instructores,
        aprendices=aprendices,
        notificaciones_no_leidas=notificaciones_no_leidas,
        sede_creada=current_user.sede,  # mostrar la sede registrada
        now=datetime.now(),
        coordinador_nombre=f"{current_user.nombre} {current_user.apellido}"
    )



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
# Editar perfil coordinador
# -------------------------------
@bp.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
@coordinador_required
def editar_perfil():
    if request.method == 'POST':
        nombre = request.form.get('nombre').strip()
        apellido = request.form.get('apellido').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo').strip().lower()
        celular = request.form.get('celular').strip()
        password = request.form.get('password')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('coordinador_bp.editar_perfil'))

        # Verificar si documento o correo ya existen en otro coordinador
        existing_coordinador = Coordinador.query.filter(
            (Coordinador.documento == documento) | (Coordinador.correo == correo)
        ).filter(Coordinador.id_coordinador != current_user.id_coordinador).first()

        if existing_coordinador:
            flash('Documento o correo ya están en uso por otro coordinador.', 'danger')
            return redirect(url_for('coordinador_bp.editar_perfil'))

        # Actualizar datos
        current_user.nombre = nombre
        current_user.apellido = apellido
        current_user.tipo_documento = tipo_documento
        current_user.documento = documento
        current_user.correo = correo
        current_user.celular = celular

        if password:
            from werkzeug.security import generate_password_hash
            current_user.password = generate_password_hash(password)

        try:
            db.session.commit()
            flash('Perfil actualizado correctamente.', 'success')
            return redirect(url_for('coordinador_bp.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar perfil: {str(e)}', 'danger')

    return render_template('coordinador/editar_perfil.html', coordinador=current_user, now=datetime.now())

# -------------------------------
# Crear/Editar sede
# -------------------------------
@bp.route('/crear_sede', methods=['GET', 'POST'])
@login_required
@coordinador_required
def crear_sede():
    # Lista de sedes definidas en el Enum
    opciones_sede = Sede.__table__.columns['nombre_sede'].type.enums  

    sede_existente = getattr(current_user, 'sede', None)

    if request.method == 'POST':
        nombre_sede = request.form.get('nombre_sede')
        ciudad = request.form.get('ciudad')
        token_input = request.form.get('token')

        if sede_existente:
            # --- MODO EDICIÓN ---
            if not all([nombre_sede, ciudad]):
                flash("Nombre de sede y ciudad son obligatorios", "error")
                return render_template('crear_sede.html', sede=sede_existente, modo='editar',
                                       opciones_sede=opciones_sede, now=datetime.now())

            try:
                sede_existente.nombre_sede = nombre_sede
                sede_existente.ciudad = ciudad
                db.session.commit()

                flash(f"Sede '{sede_existente.nombre_sede}' actualizada exitosamente.", "success")
                return redirect(url_for('coordinador_bp.dashboard'))

            except Exception as e:
                db.session.rollback()
                flash(f"Ocurrió un error al actualizar la sede: {str(e)}", "error")
                return render_template('crear_sede.html', sede=sede_existente, modo='editar',
                                       opciones_sede=opciones_sede, now=datetime.now())

        else:
            # --- MODO CREACIÓN ---
            if not all([nombre_sede, ciudad, token_input]):
                flash("Token, nombre de sede y ciudad son obligatorios", "error")
                return render_template('crear_sede.html', opciones_sede=opciones_sede, now=datetime.now())

            token_obj = TokenCoordinador.query.filter_by(token=token_input).first()
            if not token_obj:
                flash("Token inválido", "error")
                return render_template('crear_sede.html', opciones_sede=opciones_sede, now=datetime.now())

            if not token_obj.usado:
                flash("El token aún no ha sido usado para registrar al coordinador", "error")
                return render_template('crear_sede.html', opciones_sede=opciones_sede, now=datetime.now())

            if getattr(token_obj, 'usado_para_sede', False):
                flash("Este token ya se ha usado para registrar una sede", "error")
                return render_template('crear_sede.html', opciones_sede=opciones_sede, now=datetime.now())

            try:
                sede = Sede(nombre_sede=nombre_sede, ciudad=ciudad)
                db.session.add(sede)
                db.session.commit()

                current_user.sede_id = sede.id_sede
                token_obj.usado_para_sede = True
                db.session.add(current_user)
                db.session.commit()

                flash(f"Sede '{sede.nombre_sede}' creada exitosamente.", "success")
                return redirect(url_for('coordinador_bp.dashboard'))

            except Exception as e:
                db.session.rollback()
                flash(f"Ocurrió un error al registrar la sede: {str(e)}", "error")
                return render_template('crear_sede.html', opciones_sede=opciones_sede, now=datetime.now())

    # GET → renderizar formulario
    if sede_existente:
        return render_template('crear_sede.html', sede=sede_existente, modo='editar',
                               opciones_sede=opciones_sede, now=datetime.now())
    else:
        return render_template('crear_sede.html', opciones_sede=opciones_sede, now=datetime.now())

