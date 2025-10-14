from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from app.models.users import Aprendiz, Instructor, Notificacion , Evidencia, Coordinador, Administrador, Programa
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta, date
from sqlalchemy import or_
import os
from flask import current_app
from werkzeug.utils import secure_filename

bp = Blueprint('aprendiz_bp', __name__, url_prefix='/aprendiz')

# -------------------------------
# Decorador para proteger rutas de aprendiz
# -------------------------------
def aprendiz_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("No tienes permisos para acceder a esta sección", "error")
            return redirect(url_for('aprendiz_bp.login'))
        
        # Permitir al instructor acceder al dashboard de cualquier aprendiz
        if hasattr(current_user, "id_aprendiz"):
            return f(*args, **kwargs)
        elif hasattr(current_user, "id_instructor") and 'id' in kwargs:
            return f(*args, **kwargs)
        else:
            flash("No tienes permisos para acceder a esta sección", "error")
            return redirect(url_for('aprendiz_bp.login'))
    return decorated_function


# -------------------------------
# Función para enviar notificación
# -------------------------------
def enviar_notificacion(mensaje, destinatario_id=None, rol_destinatario=None):
    noti = Notificacion(
        mensaje=mensaje,
        remitente_id=current_user.id_aprendiz,
        rol_remitente="Aprendiz",
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
        from app.models.users import Coordinador
        remitente = Coordinador.query.filter_by(id_coordinador=noti.remitente_id).first()
        if remitente:
            return f"{remitente.nombre} {remitente.apellido}"
    elif role == "Instructor":
        from app.models.users import Instructor
        remitente = Instructor.query.filter_by(id_instructor=noti.remitente_id).first()
        if remitente:
            return f"{remitente.nombre_instructor} {remitente.apellido_instructor}"
    elif role == "Aprendiz":
        remitente = Aprendiz.query.filter_by(id_aprendiz=noti.remitente_id).first()
        if remitente:
            return f"{remitente.nombre} {remitente.apellido}"
    elif role == "Administrador":
        from app.models.users import Administrador
        remitente = Administrador.query.filter_by(id_admin=noti.remitente_id).first()
        if remitente:
            return f"{getattr(remitente, 'nombre', 'Administrador')} {getattr(remitente, 'apellido', '')}".strip()

    return "Sistema"

# -------------------------------
# Registro de aprendiz
# -------------------------------
@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        correo = request.form.get('correo')
        celular = request.form.get('celular')
        password = request.form.get('password')
        sede_id_form = request.form.get('sede_id')
        ficha = request.form.get('ficha')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular, password, ficha]):
            flash("Todos los campos son obligatorios", "error")
            return render_template('aprendiz/registro.html', now=datetime.now())

        # Verificar unicidad global (todos los tipos de usuario)
        from app.models.users import Administrador, Coordinador, Instructor

        # Verificar documento en todos los modelos
        documento_existe = (Aprendiz.query.filter_by(documento=documento).first() or
                           Administrador.query.filter_by(documento=documento).first() or
                           Coordinador.query.filter_by(documento=documento).first() or
                           Instructor.query.filter_by(documento=documento).first())

        # Verificar email (solo en modelos que tienen email)
        email_existe = (Aprendiz.query.filter_by(correo=correo).first() or
                       Coordinador.query.filter_by(correo=correo).first() or
                       Instructor.query.filter_by(correo_instructor=correo).first())

        # Verificar celular (solo en modelos que tienen celular)
        celular_existe = (Aprendiz.query.filter_by(celular=celular).first() or
                         Coordinador.query.filter_by(celular=celular).first() or
                         Instructor.query.filter_by(celular_instructor=celular).first())

        if documento_existe:
            flash("Ya existe un usuario con ese documento", "error")
            return render_template('aprendiz/registro.html', sedes=sedes, now=datetime.now())

        if email_existe:
            flash("Ya existe un usuario con ese email", "error")
            return render_template('aprendiz/registro.html', sedes=sedes, now=datetime.now())

        if celular_existe:
            flash("Ya existe un usuario con ese número de celular", "error")
            return render_template('aprendiz/registro.html', sedes=sedes, now=datetime.now())
        password_hash = generate_password_hash(password)

        # Verificar instructor actual y su sede
        if not current_user or not hasattr(current_user, "id_instructor"):
            flash("Error: solo un instructor puede registrar aprendices.", "error")
            return render_template('aprendiz/registro.html', now=datetime.now())

        instructor = Instructor.query.get(current_user.id_instructor)
        if not instructor or not instructor.sede_id:
            flash("El instructor no tiene una sede válida asignada.", "error")
            return render_template('aprendiz/registro.html', now=datetime.now())

        # Usar sede del formulario si se proporciona, sino la del instructor
        sede_id_final = int(sede_id_form) if sede_id_form else instructor.sede_id

        # Buscar programa existente por ficha
        programa = Programa.query.filter_by(ficha=int(ficha)).first()
        if not programa:
            flash("La ficha especificada no existe en el sistema.", "error")
            from app.models.users import Sede
            sedes = Sede.query.all()
            return render_template('aprendiz/registro.html', sedes=sedes, now=datetime.now())

        aprendiz = Aprendiz(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            correo=correo,
            celular=celular,
            password=password_hash,
            instructor_id=instructor.id_instructor,
            coordinador_id=instructor.coordinador_id,  # [OK] opcional pero útil
            sede_id=sede_id_final,
            programa_id=programa.id_programa
        )

        try:
            db.session.add(aprendiz)
            db.session.commit()
            flash("Registro exitoso. Ahora inicia sesión", "modal")
            return redirect(url_for('aprendiz_bp.login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Ocurrió un error al registrar: {str(e)}", "error")
            from app.models.users import Sede
            sedes = Sede.query.all()
            return render_template('aprendiz/registro.html', sedes=sedes, now=datetime.now())

    # Mostrar TODAS las sedes disponibles para que el aprendiz pueda elegir
    from app.models.users import Sede
    sedes = Sede.query.all()

    return render_template('aprendiz/registro.html', sedes=sedes, now=datetime.now())

# -------------------------------
# Login del aprendiz
# -------------------------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        documento = request.form.get('documento')
        password = request.form.get('password')

        aprendiz = Aprendiz.query.filter_by(documento=documento).first()
        if not aprendiz or not check_password_hash(aprendiz.password, password):
            flash("Documento o contraseña incorrectos", "error")
            return render_template('aprendiz/login.html', now=datetime.now())

        login_user(aprendiz)

        flash("Inicio de sesión exitoso. Bienvenido al sistema.", "modal")
        return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))

    return render_template('login.html', now=datetime.now())

# -------------------------------
# Logout del aprendiz
# -------------------------------
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión", "modal")
    return redirect(url_for('aprendiz_bp.login'))

# -------------------------------
# Dashboard del aprendiz
# -------------------------------
@bp.route('/dashboard/', defaults={'aprendiz_id': None})
@bp.route('/dashboard/<int:aprendiz_id>', methods=['GET'])
@login_required
def dashboard_aprendiz(aprendiz_id):
    # -----------------------------
    # Determinar qué aprendiz se muestra
    # -----------------------------
    if isinstance(current_user, Aprendiz):
        if aprendiz_id is None or aprendiz_id == current_user.id_aprendiz:
            aprendiz_obj = current_user
        else:
            flash("No tienes permiso para acceder a este dashboard.", "danger")
            return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))
    elif isinstance(current_user, Instructor) and aprendiz_id is not None:
        aprendiz_obj = Aprendiz.query.get_or_404(aprendiz_id)
        if aprendiz_obj.instructor_id != current_user.id_instructor:
            flash("No tienes permiso para ver este aprendiz.", "danger")
            return redirect(url_for('instructor_bp.dashboard_instructor', instructor_id=current_user.id_instructor))
    else:
        flash("No tienes permiso para acceder a este dashboard.", "danger")
        return redirect(url_for('auth.login'))

    # -----------------------------
    # Progreso de evidencias
    # -----------------------------
    total_requerido = 17
    evidencias_subidas = (
        db.session.query(Evidencia)
        .filter_by(aprendiz_id_aprendiz=aprendiz_obj.id_aprendiz)
        .filter(Evidencia.fecha_subida.isnot(None), Evidencia.url_archivo != '')
        .count()
    )
    progreso = int((evidencias_subidas / total_requerido) * 100) if total_requerido > 0 else 0

    # -----------------------------
    # Progreso en tiempo según contrato
    # -----------------------------
    contrato = aprendiz_obj.contrato
    progreso_tiempo = 0
    if contrato and contrato.fecha_inicio and contrato.fecha_fin:
        fecha_inicio = contrato.fecha_inicio.date() if hasattr(contrato.fecha_inicio, "date") else contrato.fecha_inicio
        fecha_fin = contrato.fecha_fin.date() if hasattr(contrato.fecha_fin, "date") else contrato.fecha_fin
        total_dias = (fecha_fin - fecha_inicio).days
        dias_transcurridos = (date.today() - fecha_inicio).days
        if total_dias > 0:
            progreso_tiempo = round((dias_transcurridos / total_dias) * 100, 2)
            progreso_tiempo = min(max(progreso_tiempo, 0), 100)

    # -----------------------------
    # Notificaciones no leídas (ahora usa aprendiz_obj)
    # -----------------------------
    notificaciones_no_leidas = Notificacion.query.filter(
        Notificacion.rol_destinatario == 'Aprendiz',
        Notificacion.visto == False
    ).filter(
        or_(
            Notificacion.destinatario_id == aprendiz_obj.id_aprendiz,
            Notificacion.destinatario_id == None  # solo si es global
        )
    ).count()

    # -----------------------------
    # Usuarios para mensajes (solo si es Aprendiz)
    # -----------------------------
    usuarios = {}
    es_aprendiz = isinstance(current_user, Aprendiz)
    if es_aprendiz:
        # Filtrar instructor asignado
        usuarios['Instructor'] = Instructor.query.filter_by(id_instructor=current_user.instructor_id).all() if current_user.instructor_id else []
        # Filtrar coordinador de la sede
        usuarios['Coordinador'] = Coordinador.query.filter_by(sede_id=current_user.sede_id).all() if current_user.sede_id else []
        # Administradores todos
        usuarios['Administrador'] = Administrador.query.all()

    # -----------------------------
    # Renderizar template
    # -----------------------------
    return render_template(
        'dasboardh_aprendiz.html',
        aprendiz=aprendiz_obj,
        progreso=progreso,
        progreso_tiempo=progreso_tiempo,
        contrato=contrato,
        notificaciones_no_leidas=notificaciones_no_leidas,
        es_aprendiz=es_aprendiz,
        now=datetime.now(),
        usuarios=usuarios
    )

# -------------------------------
# Editar aprendiz
# -------------------------------
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@aprendiz_required
def editar_aprendiz(id):
    if id != current_user.id_aprendiz:
        flash("No puedes editar este perfil", "error")
        return redirect(url_for('aprendiz_bp.dashboard_aprendiz', aprendiz_id=current_user.id_aprendiz))

    aprendiz = Aprendiz.query.get_or_404(id)
    if request.method == 'POST':

        nombre = request.form.get('nombre').strip()
        apellido = request.form.get('apellido').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('email').strip().lower()
        celular = request.form.get('celular').strip()
        password = request.form.get('password')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

        aprendiz.nombre = nombre
        aprendiz.apellido = apellido
        aprendiz.tipo_documento = tipo_documento
        aprendiz.documento = documento
        aprendiz.correo = correo
        aprendiz.celular = celular
        if password:
            aprendiz.password = generate_password_hash(password)

        try:
            db.session.commit()
            flash('Perfil actualizado correctamente.', 'modal')
            # Redireccionar al dashboard del aprendiz con su id
            return redirect(url_for('aprendiz_bp.dashboard_aprendiz', aprendiz_id=aprendiz.id_aprendiz))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('perfil_aprendiz.html', aprendiz=aprendiz, mode='edit', rol_actual='Aprendiz', id_usuario=aprendiz.id_aprendiz, now=datetime.now())

# -------------------------------
# Eliminar aprendiz
# -------------------------------
@bp.route('/eliminar/<int:id>')
@login_required
@aprendiz_required
def eliminar_aprendiz(id):
    if id != current_user.id_aprendiz:
        flash("No puedes eliminar este perfil", "error")
        return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))

    aprendiz = Aprendiz.query.get_or_404(id)
    try:
        db.session.delete(aprendiz)
        db.session.commit()
        flash('Perfil eliminado exitosamente.', 'modal')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    return redirect(url_for('auth.login'))

# -------------------------------
# Perfil del aprendiz
# -------------------------------
@bp.route('/perfil/<int:aprendiz_id>')
@login_required
def perfil_aprendiz(aprendiz_id):
    aprendiz = Aprendiz.query.get_or_404(aprendiz_id)
    rol_actual = current_user.__class__.__name__
    
    # id_usuario para los botones
    if rol_actual == 'Aprendiz':
        id_usuario = current_user.id_aprendiz
    else:
        id_usuario = aprendiz.id_aprendiz

    return render_template(
        "perfil_aprendiz.html",
        aprendiz=aprendiz,
        rol_actual=rol_actual,
        id_usuario=id_usuario,
        mode='view'
    )



# -------------------------------
# Enviar mensaje
# -------------------------------
@bp.route('/enviar_mensaje', methods=['POST'])
@login_required
@aprendiz_required
def enviar_mensaje():
    rol_destinatario = request.form.get('rol_destinatario')
    destinatario_id = request.form.get('destinatario_id')
    motivo = request.form.get('motivo')  # opcional si lo quieres usar como en admin
    mensaje = request.form.get('mensaje')

    if not rol_destinatario or not mensaje:
        flash("Debes seleccionar un destinatario y escribir un mensaje.", "error")
        return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))

    # [OK] Caso 1: mensaje a usuario específico
    if destinatario_id:
        destinatario_id = int(destinatario_id)

        user = None
        if rol_destinatario == "Coordinador":
            user = Coordinador.query.get(destinatario_id)
        elif rol_destinatario == "Instructor":
            user = Instructor.query.get(destinatario_id)
        elif rol_destinatario == "Administrador":
            user = Administrador.query.get(destinatario_id)

        if user:
            # Validar permisos según rol
            if rol_destinatario == "Instructor" and user.id_instructor != current_user.instructor_id:
                flash("Solo puedes enviar mensajes a tu instructor asignado.", "error")
                return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))
            elif rol_destinatario == "Coordinador" and user.sede_id != current_user.sede_id:
                flash("Solo puedes enviar mensajes al coordinador de tu sede.", "error")
                return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))

            # Nombre completo según rol
            if rol_destinatario == "Instructor":
                nombre_completo = f"{user.nombre_instructor} {user.apellido_instructor}"
            else:
                nombre_completo = f"{user.nombre} {user.apellido}"

            enviar_notificacion(
                mensaje=f"[{motivo}] {mensaje}" if motivo else mensaje,
                destinatario_id=destinatario_id,
                rol_destinatario=rol_destinatario
            )

            flash(
                f"Mensaje enviado con éxito a {nombre_completo} ({rol_destinatario}).",
                "success"
            )
        else:
            flash("El destinatario no existe o no pertenece a ese rol.", "error")

    # [OK] Caso 2: mensaje general al rol completo
    else:
        enviar_notificacion(
            mensaje=f"[{motivo}] {mensaje}" if motivo else mensaje,
            destinatario_id=None,
            rol_destinatario=rol_destinatario
        )
        flash(f"Mensaje general enviado a todos los {rol_destinatario.lower()}s.", "success")

    return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))


# -------------------------------
# Listar notificaciones
# -------------------------------
@bp.route('/notificaciones')
@login_required
@aprendiz_required
def notificaciones():
    pagina = request.args.get('pagina', 1, type=int)
    per_page = 10

    # Filtrar notificaciones que sean individuales o globales
    pagination = Notificacion.query.filter(
        Notificacion.rol_destinatario == "Aprendiz",
        ((Notificacion.destinatario_id == current_user.id_aprendiz) |
         (Notificacion.destinatario_id == None))
    ).order_by(Notificacion.fecha_creacion.desc()).paginate(
        page=pagina, per_page=per_page, error_out=False
    )

    notificaciones = pagination.items
    total_paginas = pagination.pages

    # Asignar remitente
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
# Ver notificación
# -------------------------------
@bp.route('/notificacion/<int:noti_id>')
@login_required
@aprendiz_required
def ver_notificacion(noti_id):
    # Solo puede ver notificación que le pertenece
    noti = Notificacion.query.filter(
        Notificacion.id == noti_id,
        Notificacion.rol_destinatario == 'Aprendiz',
        Notificacion.destinatario_id == current_user.id_aprendiz
    ).first_or_404()

    if not noti.visto:
        noti.visto = True
        db.session.commit()

    remitente_nombre = obtener_remitente(noti)
    fecha_local = noti.fecha_creacion - timedelta(hours=5)

    return render_template(
        'notificacion/ver_notificacion.html',
        notificacion=noti,
        remitente_nombre=remitente_nombre,
        now=datetime.now(),
        fecha_local=fecha_local
    )

# -------------------------------
# Responder notificación
# -------------------------------
@bp.route('/notificacion/<int:noti_id>/responder', methods=['GET', 'POST'])
@login_required
@aprendiz_required
def responder_notificacion(noti_id):
    noti = Notificacion.query.filter_by(
        id=noti_id,
        rol_destinatario='Aprendiz',
        destinatario_id=current_user.id_aprendiz
    ).first_or_404()

    if request.method == 'POST':
        respuesta = request.form.get('respuesta')

        remitente_id = current_user.id_aprendiz

        if respuesta and remitente_id:
            nueva = Notificacion(
                mensaje=f"[Respuesta a '{noti.mensaje.split(']')[0].replace('[','')}'] {respuesta}",
                remitente_id=remitente_id,
                rol_remitente="Aprendiz",
                destinatario_id=noti.remitente_id,
                rol_destinatario=noti.rol_remitente
            )
            db.session.add(nueva)
            db.session.commit()
            flash('Respuesta enviada con éxito.', 'modal')
            return redirect(url_for("aprendiz_bp.ver_notificacion", noti_id=noti.id))
        else:
            flash('No se pudo enviar la respuesta. Asegúrate de escribir un mensaje.', 'danger')

    return redirect(url_for('aprendiz_bp.notificaciones'))

# -------------------------------
# Marcar todas notificaciones
# -------------------------------
@bp.route('/marcar_todas_notificaciones', methods=['POST'])
@login_required
@aprendiz_required
def marcar_todas_notificaciones():
    Notificacion.query.filter_by(
        rol_destinatario='Aprendiz',
        destinatario_id=current_user.id_aprendiz,
        visto=False
    ).update({Notificacion.visto: True})
    db.session.commit()
    flash('Todas las notificaciones han sido marcadas como vistas.', 'modal')
    return redirect(url_for('aprendiz_bp.notificaciones'))

# -------------------------------
# Subir evidencia (solo Aprendiz)
# -------------------------------
@bp.route('/subir_evidencia/<int:num>', methods=['POST'])
@login_required
def subir_evidencia(num):
    # Solo el aprendiz puede subir
    if not isinstance(current_user, Aprendiz):
        flash("No tienes permisos para subir evidencias.", "danger")
        return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))

    archivo = request.files.get('archivo')

    if not archivo or archivo.filename == '':
        flash("Debe seleccionar un archivo válido", "danger")
        return render_template("aprendiz/subir_evidencia.html", now=datetime.now())

    total_requerido = 17
    evidencias_subidas = Evidencia.query.filter_by(
        aprendiz_id_aprendiz=current_user.id_aprendiz
    ).count()

    if evidencias_subidas >= total_requerido:
        flash("Ya subiste todas las evidencias requeridas.", "danger")
        return render_template("aprendiz/subir_evidencia.html", now=datetime.now())

    original_name = secure_filename(archivo.filename)
    extension = os.path.splitext(original_name)[1].lower()

    filename = f"evidencia_{current_user.id_aprendiz}_{num}_{datetime.now().strftime('%Y%m%d%H%M%S')}{extension}"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    archivo.save(path)

    evidencia = Evidencia(
        aprendiz_id_aprendiz=current_user.id_aprendiz,
        num_evidencia=num,
        url_archivo=filename,
        fecha_subida=datetime.now()
    )
    db.session.add(evidencia)
    db.session.commit()

    flash("Evidencia subida con éxito", "modal")
    return render_template("aprendiz/subir_evidencia.html", now=datetime.now())


# -------------------------------
# Ver evidencias (Aprendiz o Instructor)
# -------------------------------
@bp.route('/ver_evidencias/<int:aprendiz_id>')
@login_required
def ver_evidencias(aprendiz_id):
    from app.models.users import Aprendiz
    aprendiz = Aprendiz.query.get_or_404(aprendiz_id)

    # Solo Aprendiz propietario o Instructor puede ver
    if isinstance(current_user, Aprendiz) and current_user.id_aprendiz != aprendiz.id_aprendiz:
        flash("No tienes permisos para ver estas evidencias.", "danger")
        return redirect(url_for('aprendiz_bp.dashboard_aprendiz'))
    elif isinstance(current_user, Instructor):
        if aprendiz.instructor_id != current_user.id_instructor:
            flash("No tienes permisos para ver estas evidencias.", "danger")
            return redirect(url_for('instructor_bp.dashboard_instructor'))

    evidencias = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz).all()

    return render_template(
        "aprendiz/ver_evidencias.html",
        aprendiz=aprendiz,
        evidencias=evidencias,
        now=datetime.now()
    )

