from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models.users import (
    AdministradorSede, Instructor, Notificacion, Aprendiz,
    Administrador, Programa, Ficha, Sede
)
from app import db
from datetime import datetime, timedelta
from functools import wraps
import logging
from sqlalchemy.orm import joinedload

adm_sede_bp = Blueprint('adm_sede_bp', __name__, url_prefix='/adm_sede')

# -------------------------------
# Decorador para proteger rutas de administrador de sede
# -------------------------------
def admin_sede_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, AdministradorSede):
            flash("No tienes permisos para acceder a esta sección", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------
# Función para enviar notificación
# -------------------------------
def enviar_notificacion(mensaje, destinatario_id=None, rol_destinatario=None, motivo=None):
    noti = Notificacion(
        mensaje=mensaje,
        motivo=motivo,
        remitente_id=current_user.id_admin_sede,
        rol_remitente="AdministradorSede",
        destinatario_id=destinatario_id,
        rol_destinatario=rol_destinatario,
        visto=False
    )
    db.session.add(noti)
    db.session.commit()
    return True

# -------------------------------
# Función para obtener nombre del remitente
# -------------------------------
def obtener_remitente(noti):
    """
    Devuelve el nombre simple del remitente (sin prefijos como 'De: ').
    Si no se encuentra el remitente, devuelve 'Sistema'.
    """
    role = (noti.rol_remitente or "").strip()

    if role == "Instructor":
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
            return f"{remitente.nombre} {remitente.apellido}"
    elif role == "AdministradorSede":
        remitente = AdministradorSede.query.filter_by(id_admin_sede=noti.remitente_id).first()
        if remitente:
            return f"{remitente.nombre} {remitente.apellido}"

    # Si no hay remitente encontrado o rol desconocido -> "Sistema"
    return "Sistema"

# -------------------------------
# Dashboard administrador de sede
# -------------------------------
@adm_sede_bp.route('/dashboard')
@login_required
@admin_sede_required
def dashboard():
    # Instructores registrados por este admin de sede
    instructores = Instructor.query.filter_by(administrador_sede_id=current_user.id_admin_sede).all()

    # Aprendices en la sede
    aprendices = Aprendiz.query.filter_by(sede_id=current_user.sede_id).all()

    # Programas y fichas asociados a la sede
    programas = Programa.query.join(Ficha).filter(Ficha.sede_id == current_user.sede_id).all()

    # Notificaciones no leídas
    notificaciones_no_leidas = Notificacion.query.filter_by(
        rol_destinatario="AdministradorSede",
        visto=False
    ).count()

    administradores = Administrador.query.all()

    return render_template(
        'adm_sede/dashboard.html',
        instructores=instructores,
        aprendices=aprendices,
        programas=programas,
        notificaciones_no_leidas=notificaciones_no_leidas,
        administradores=administradores,
        now=datetime.now(),
        admin_sede_nombre=f"{current_user.nombre} {current_user.apellido}",
        sede=current_user.sede
    )


# -------------------------------
# Registrar instructor
# -------------------------------
@adm_sede_bp.route('/registrar_instructor', methods=['GET', 'POST'])
@login_required
@admin_sede_required
def registrar_instructor():
    if request.method == 'POST':
        nombre = request.form.get('nombre_instructor').strip()
        apellido = request.form.get('apellido_instructor').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo_instructor').strip().lower()
        celular = request.form.get('celular_instructor').strip()
        password = request.form.get('password')
        sede_id = current_user.sede_id # Asignar automáticamente la sede del admin de sede

        if not all([nombre, apellido, tipo_documento, documento, correo, celular, password]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('adm_sede_bp.registrar_instructor'))

        # Verificar unicidad
        documento_existe = (Instructor.query.filter_by(documento=documento).first() or
                            Administrador.query.filter_by(documento=documento).first() or
                            AdministradorSede.query.filter_by(documento=documento).first() or
                            Aprendiz.query.filter_by(documento=documento).first())

        email_existe = (Instructor.query.filter_by(correo_instructor=correo).first() or
                        Administrador.query.filter_by(correo=correo).first() or
                        AdministradorSede.query.filter_by(correo=correo).first() or
                        Aprendiz.query.filter_by(correo=correo).first())

        celular_existe = (Instructor.query.filter_by(celular_instructor=celular).first() or
                          Administrador.query.filter_by(celular=celular).first() or
                          AdministradorSede.query.filter_by(celular=celular).first() or
                          Aprendiz.query.filter_by(celular=celular).first())

        if documento_existe:
            flash('Ya existe un usuario con ese documento.', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_instructor'))

        if email_existe:
            flash('Ya existe un usuario con ese email.', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_instructor'))

        if celular_existe:
            flash('Ya existe un usuario con ese número de celular.', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_instructor'))

        hashed_password = generate_password_hash(password)

        nuevo_instructor = Instructor(
            nombre_instructor=nombre,
            apellido_instructor=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            correo_instructor=correo,
            celular_instructor=celular,
            password_instructor=hashed_password,
            administrador_sede_id=current_user.id_admin_sede,
            sede_id=sede_id
        )

        try:
            db.session.add(nuevo_instructor)
            db.session.commit()

            # Notificación a administradores principales
            administradores = Administrador.query.all()
            for admin in administradores:
                noti = Notificacion(
                    motivo="Se ha registrado un nuevo Instructor",
                    mensaje=f"{nuevo_instructor.nombre_instructor} {nuevo_instructor.apellido_instructor} en la sede {current_user.sede.nombre_completo()}",
                    remitente_id=current_user.id_admin_sede,
                    rol_remitente="AdministradorSede",
                    destinatario_id=admin.id_admin,
                    rol_destinatario="administrador",
                    visto=False
                )
                db.session.add(noti)
            db.session.commit()

            flash('Instructor registrado con éxito.', 'success')
            return redirect(url_for('adm_sede_bp.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el instructor: {str(e)}', 'danger')

    return render_template('adm_sede/registrar_instructor.html', now=datetime.now())

# -------------------------------
# Enviar mensaje
# -------------------------------
@adm_sede_bp.route('/enviar_mensaje', methods=['POST'])
@login_required
@admin_sede_required
def enviar_mensaje():
    rol_destinatario = request.form.get('rol_destinatario')
    destinatario_id = request.form.get('destinatario_id')
    motivo = request.form.get('motivo')
    mensaje = request.form.get('mensaje')
    archivo = request.files.get('archivo')

    if not rol_destinatario or not mensaje:
        flash("Debes seleccionar un destinatario y escribir un mensaje.", "error")
        return redirect(url_for('adm_sede_bp.dashboard'))

    # Manejar archivo adjunto
    if archivo and archivo.filename:
        import os
        from werkzeug.utils import secure_filename
        upload_folder = os.path.join('app', 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filename = secure_filename(archivo.filename)
        archivo_path = os.path.join(upload_folder, filename)
        archivo.save(archivo_path)
        mensaje += f"\n\nArchivo adjunto: {filename}"

    enviar_notificacion(
        mensaje=mensaje,
        motivo=motivo,
        destinatario_id=destinatario_id if destinatario_id else None,
        rol_destinatario=rol_destinatario
    )

    flash(f"Mensaje enviado a {rol_destinatario}", "success")
    return redirect(url_for('adm_sede_bp.dashboard'))

# -------------------------------
# Listar notificaciones
# -------------------------------
@adm_sede_bp.route('/notificaciones')
@login_required
@admin_sede_required
def notificaciones():
    pagina = request.args.get('pagina', 1, type=int)
    per_page = 10

    pagination = Notificacion.query.filter(
        Notificacion.rol_destinatario == "AdministradorSede",
        ((Notificacion.destinatario_id == current_user.id_admin_sede) |
         (Notificacion.destinatario_id == None))
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
# Ver notificación
# -------------------------------
@adm_sede_bp.route('/notificacion/<int:noti_id>')
@login_required
@admin_sede_required
def ver_notificacion(noti_id):
    noti = Notificacion.query.filter(
        Notificacion.id == noti_id,
        Notificacion.rol_destinatario == "AdministradorSede",
        ((Notificacion.destinatario_id == current_user.id_admin_sede) |
         (Notificacion.destinatario_id == None))
    ).first_or_404()

    if not noti.visto:
        noti.visto = True
        db.session.commit()

    # Obtener nombre del remitente
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
# Marcar todas notificaciones como vistas
# -------------------------------
@adm_sede_bp.route('/marcar_todas_notificaciones', methods=['POST'])
@login_required
@admin_sede_required
def marcar_todas_notificaciones():
    Notificacion.query.filter_by(
        rol_destinatario="AdministradorSede",
        destinatario_id=current_user.id_admin_sede,
        visto=False
    ).update({"visto": True})
    db.session.commit()
    return "", 200

# -------------------------------
# Responder notificación
# -------------------------------
@adm_sede_bp.route('/notificacion/<int:noti_id>/responder', methods=['GET', 'POST'])
@login_required
@admin_sede_required
def responder_notificacion(noti_id):
    noti = Notificacion.query.filter(
        Notificacion.id == noti_id,
        Notificacion.rol_destinatario == "AdministradorSede",
        ((Notificacion.destinatario_id == current_user.id_admin_sede) |
         (Notificacion.destinatario_id == None))
    ).first_or_404()

    if request.method == 'POST':
        motivo_respuesta = request.form.get('motivo_respuesta')
        respuesta = request.form.get('respuesta')
        archivo = request.files.get('archivo')

        if respuesta and current_user.id_admin_sede:
            mensaje_respuesta = respuesta

            # Manejar archivo adjunto
            if archivo and archivo.filename:
                import os
                from werkzeug.utils import secure_filename
                upload_folder = os.path.join('app', 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(archivo.filename)
                archivo_path = os.path.join(upload_folder, filename)
                archivo.save(archivo_path)
                mensaje_respuesta += f"\n\nArchivo adjunto: {filename}"

            nueva = Notificacion(
                motivo=motivo_respuesta,
                mensaje=mensaje_respuesta,
                remitente_id=current_user.id_admin_sede,
                rol_remitente="AdministradorSede",
                destinatario_id=noti.remitente_id,
                rol_destinatario=noti.rol_remitente
            )
            db.session.add(nueva)
            db.session.commit()
            flash('Respuesta enviada con éxito.', 'modal')
            return redirect(url_for('adm_sede_bp.ver_notificacion', noti_id=noti.id))
        else:
            flash('No se pudo enviar la respuesta. Asegúrate de escribir un mensaje.', 'danger')

    return redirect(url_for('adm_sede_bp.notificaciones'))

# -------------------------------
# Editar instructor
# -------------------------------
@adm_sede_bp.route('/editar_instructor/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_sede_required
def editar_instructor(id):
    instructor = Instructor.query.get_or_404(id)
    if instructor.administrador_sede_id != current_user.id_admin_sede:
        flash('No tienes permiso para editar este instructor.', 'danger')
        return redirect(url_for('adm_sede_bp.dashboard'))

    if request.method == 'POST':
        nombre = request.form.get('nombre_instructor').strip()
        apellido = request.form.get('apellido_instructor').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo_instructor').strip().lower()
        celular = request.form.get('celular_instructor').strip()
        password = request.form.get('password')

        if not all([nombre, apellido, documento, correo, celular]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('adm_sede_bp.editar_instructor', id=id))

        # Verificar unicidad
        existing = Instructor.query.filter(
            (Instructor.documento == documento) | (Instructor.correo_instructor == correo) | (Instructor.celular_instructor == celular)
        ).filter(Instructor.id_instructor != id).first()

        if existing:
            flash('Documento, correo o celular ya están en uso.', 'danger')
            return redirect(url_for('adm_sede_bp.editar_instructor', id=id))

        instructor.nombre_instructor = nombre
        instructor.apellido_instructor = apellido
        instructor.documento = documento
        instructor.correo_instructor = correo
        instructor.celular_instructor = celular
        if password:
            instructor.password_instructor = generate_password_hash(password)

        try:
            db.session.commit()
            flash('Instructor actualizado correctamente.', 'success')
            return redirect(url_for('adm_sede_bp.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('adm_sede/editar_instructor.html', instructor=instructor, now=datetime.now())

# -------------------------------
# Eliminar instructor
# -------------------------------
@adm_sede_bp.route('/eliminar_instructor/<int:id>', methods=['POST'])
@login_required
@admin_sede_required
def eliminar_instructor(id):
    instructor = Instructor.query.get_or_404(id)
    if instructor.administrador_sede_id != current_user.id_admin_sede:
        flash('No tienes permiso para eliminar este instructor.', 'danger')
        return redirect(url_for('adm_sede_bp.dashboard'))

    try:
        db.session.delete(instructor)
        db.session.commit()
        flash('Instructor eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar instructor: {str(e)}', 'danger')

    return redirect(url_for('adm_sede_bp.dashboard'))

# -------------------------------
# Registrar programa
# -------------------------------
@adm_sede_bp.route('/registrar_programa', methods=['GET', 'POST'])
@login_required
@admin_sede_required
def registrar_programa():
    if request.method == 'GET':
        return redirect(url_for('adm_sede_bp.gestionar_programas'))
    if request.method == 'POST':
        nombre_programa = request.form.get('nombre_programa').strip()
        titulo = request.form.get('titulo')
        numero_ficha = request.form.get('numero_ficha').strip()

        if not all([nombre_programa, titulo, numero_ficha]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('adm_sede_bp.gestionar_programas'))

        try:
            numero_ficha_int = int(numero_ficha)
        except ValueError:
            flash('El número de ficha debe ser un número entero válido.', 'danger')
            return redirect(url_for('adm_sede_bp.gestionar_programas'))

        # Buscar o crear ficha
        ficha = Ficha.query.filter_by(numero_ficha=numero_ficha_int).first()
        if not ficha:
            ficha = Ficha(numero_ficha=numero_ficha_int, sede_id=current_user.sede_id)
            db.session.add(ficha)
            db.session.flush()  # Para obtener el id_ficha
        elif ficha.sede_id is None:
            ficha.sede_id = current_user.sede_id
            db.session.flush()

        nuevo_programa = Programa(
            nombre_programa=nombre_programa,
            titulo=titulo,
            ficha_id=ficha.id_ficha,
            instructor_id_instructor=None
        )

        try:
            db.session.add(nuevo_programa)
            db.session.commit()
            flash('Programa registrado correctamente.', 'success')
            return redirect(url_for('adm_sede_bp.gestionar_programas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_programa'))

    return render_template('adm_sede/registrar_programa.html', now=datetime.now())

# -------------------------------
# Editar programa
# -------------------------------
@adm_sede_bp.route('/editar_programa/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_sede_required
def editar_programa(id):
    programa = Programa.query.get_or_404(id)
    # Verificar que el programa pertenezca a la sede del admin
    if programa.ficha_rel and programa.ficha_rel.sede_id != current_user.sede_id:
        flash('No tienes permiso para editar este programa.', 'danger')
        return redirect(url_for('adm_sede_bp.dashboard'))

    if request.method == 'POST':
        # Verificar nuevamente en POST
        if programa.ficha_rel and programa.ficha_rel.sede_id != current_user.sede_id:
            flash('No tienes permiso para editar este programa.', 'danger')
            return redirect(url_for('adm_sede_bp.dashboard'))

        nombre_programa = request.form.get('nombre_programa').strip()
        titulo = request.form.get('titulo')
        numero_ficha = request.form.get('numero_ficha').strip()

        if not all([nombre_programa, titulo, numero_ficha]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('adm_sede_bp.editar_programa', id=id))

        try:
            numero_ficha_int = int(numero_ficha)
        except ValueError:
            flash('El número de ficha debe ser un número entero válido.', 'danger')
            return redirect(url_for('adm_sede_bp.editar_programa', id=id))

        ficha = Ficha.query.filter_by(numero_ficha=numero_ficha_int).first()
        if not ficha:
            flash('Ficha no encontrada.', 'danger')
            return redirect(url_for('adm_sede_bp.editar_programa', id=id))

        programa.nombre_programa = nombre_programa
        programa.titulo = titulo
        programa.ficha_id = ficha.id_ficha

        try:
            db.session.commit()
            flash('Programa actualizado correctamente.', 'success')
            return redirect(url_for('adm_sede_bp.gestionar_programas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('adm_sede/editar_programa.html', programa=programa, now=datetime.now())

# -------------------------------
# Eliminar programa
# -------------------------------
@adm_sede_bp.route('/eliminar_programa/<int:id>', methods=['POST'])
@login_required
@admin_sede_required
def eliminar_programa(id):
    programa = Programa.query.get_or_404(id)
    if programa.ficha_rel and programa.ficha_rel.sede_id != current_user.sede_id:
        flash('No tienes permiso para eliminar este programa.', 'danger')
        return redirect(url_for('adm_sede_bp.dashboard'))

    try:
        db.session.delete(programa)
        db.session.commit()
        flash('Programa eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar programa: {str(e)}', 'danger')

    return redirect(url_for('adm_sede_bp.dashboard'))

# -------------------------------
# Gestionar Instructores
# -------------------------------
@adm_sede_bp.route('/gestionar_instructores')
@login_required
@admin_sede_required
def gestionar_instructores():
    instructores = Instructor.query.filter_by(administrador_sede_id=current_user.id_admin_sede).all()
    return render_template('adm_sede/gestionar_instructores.html', instructores=instructores, now=datetime.now())

# -------------------------------
# Gestionar Programas
# -------------------------------
@adm_sede_bp.route('/gestionar_programas')
@login_required
@admin_sede_required
def gestionar_programas():
    logging.info(f"Gestionando programas para sede_id={current_user.sede_id}")
    programas = Programa.query.join(Ficha).options(joinedload(Programa.ficha_rel)).filter(Ficha.sede_id == current_user.sede_id).all()
    logging.info(f"Programas encontrados: {len(programas)}")
    return render_template('adm_sede/gestionar_programas.html', programas=programas, now=datetime.now())

# -------------------------------
# Gestionar Aprendices
# -------------------------------
@adm_sede_bp.route('/gestionar_aprendices')
@login_required
@admin_sede_required
def gestionar_aprendices():
    search = request.args.get('search', '').strip()
    # Incluir aprendices en la sede del administrador
    query = Aprendiz.query.filter_by(sede_id=current_user.sede_id).options(
        joinedload(Aprendiz.programa).joinedload(Programa.ficha_rel),
        joinedload(Aprendiz.instructor)
    )

    if search:
        query = query.filter(Aprendiz.documento.ilike(f'%{search}%'))

    aprendices = query.all()

    # Agrupar aprendices por jornada
    aprendices_manana = [a for a in aprendices if a.jornada == 'Mañana']
    aprendices_tarde = [a for a in aprendices if a.jornada == 'Tarde']
    aprendices_noche = [a for a in aprendices if a.jornada == 'Noche']

    # Obtener instructores disponibles para asignación
    instructores = Instructor.query.filter_by(sede_id=current_user.sede_id).all()

    return render_template('adm_sede/gestionar_aprendices.html',
                          aprendices=aprendices,
                          aprendices_manana=aprendices_manana,
                          aprendices_tarde=aprendices_tarde,
                          aprendices_noche=aprendices_noche,
                          instructores=instructores,
                          search=search,
                          now=datetime.now())

# -------------------------------
# Asignar Instructor a Aprendiz (desde lista)
# -------------------------------
@adm_sede_bp.route('/asignar_instructor_lista', methods=['POST'])
@login_required
@admin_sede_required
def asignar_instructor_lista():
    aprendiz_id = request.form.get('aprendiz_id')
    instructor_id = request.form.get('instructor_id')

    aprendiz = Aprendiz.query.get_or_404(aprendiz_id)
    if aprendiz.sede_id != current_user.sede_id:
        flash('No tienes permiso para asignar instructor a este aprendiz.', 'danger')
        return redirect(url_for('adm_sede_bp.gestionar_aprendices'))

    if instructor_id:
        instructor = Instructor.query.get(int(instructor_id))
        if instructor and instructor.administrador_sede_id == current_user.id_admin_sede:
            aprendiz.instructor_id = int(instructor_id)
            db.session.commit()
            flash('Instructor asignado correctamente.', 'success')
        else:
            flash('Instructor no válido.', 'danger')
    else:
        flash('No se puede remover el instructor, ya que la sede es obligatoria.', 'danger')

    return redirect(url_for('adm_sede_bp.gestionar_aprendices'))

# -------------------------------
# Registrar Aprendiz
# -------------------------------
@adm_sede_bp.route('/registrar_aprendiz', methods=['GET', 'POST'])
@login_required
@admin_sede_required
def registrar_aprendiz():
    if request.method == 'POST':
        nombre = request.form.get('nombre').strip()
        apellido = request.form.get('apellido').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo').strip().lower()
        celular = request.form.get('celular').strip()
        password = request.form.get('password')
        numero_ficha = request.form.get('numero_ficha').strip()
        jornada = request.form.get('jornada')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular, password, numero_ficha, jornada]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('adm_sede_bp.registrar_aprendiz'))

        try:
            numero_ficha_int = int(numero_ficha)
        except ValueError:
            flash('El número de ficha debe ser un número entero válido.', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_aprendiz'))

        # Validar que la ficha exista
        ficha = Ficha.query.filter_by(numero_ficha=numero_ficha_int).first()
        if not ficha:
            flash('Error: Ficha no encontrada.', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_aprendiz'))
        logging.info(f"Ficha encontrada: id={ficha.id_ficha}, sede_id={ficha.sede_id}")

        # Obtener programa de la ficha
        programa = Programa.query.filter_by(ficha_id=ficha.id_ficha).first()
        if not programa:
            flash('Error: La ficha no tiene un programa asignado.', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_aprendiz'))
        logging.info(f"Programa encontrado: id={programa.id_programa}, instructor_id={programa.instructor_id_instructor}")

        # Determinar sede_id de la ficha
        sede_id = ficha.sede_id
        logging.info(f"Sede_id determinado: {sede_id}")
        logging.info(f"Instructor asignado posteriormente por admin, no desde programa")
        if sede_id != current_user.sede_id:
            flash('La ficha pertenece a una sede diferente. No puede registrar aprendices para esta ficha.', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_aprendiz'))

        # Verificar unicidad
        documento_existe = (Aprendiz.query.filter_by(documento=documento).first() or
                            Administrador.query.filter_by(documento=documento).first() or
                            AdministradorSede.query.filter_by(documento=documento).first() or
                            Instructor.query.filter_by(documento=documento).first())

        correo_existe = (Aprendiz.query.filter_by(correo=correo).first() or
                         Administrador.query.filter_by(correo=correo).first() or
                         AdministradorSede.query.filter_by(correo=correo).first() or
                         Instructor.query.filter_by(correo_instructor=correo).first())

        celular_existe = (Aprendiz.query.filter_by(celular=celular).first() or
                          Administrador.query.filter_by(celular=celular).first() or
                          AdministradorSede.query.filter_by(celular=celular).first() or
                          Instructor.query.filter_by(celular_instructor=celular).first())

        if documento_existe:
            flash('Ya existe un usuario con ese documento.', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_aprendiz'))

        if correo_existe:
            flash('Ya existe un usuario con ese correo.', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_aprendiz'))

        if celular_existe:
            flash('Ya existe un usuario con ese número de celular.', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_aprendiz'))

        hashed_password = generate_password_hash(password)

        logging.info(f"Registrando aprendiz: ficha={numero_ficha_int}, sede_id={sede_id}, programa_id={programa.id_programa}, instructor_id=None (asignado posteriormente)")

        nuevo_aprendiz = Aprendiz(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            correo=correo,
            celular=celular,
            jornada=jornada,
            password_aprendiz=hashed_password,
            programa_id=programa.id_programa,
            instructor_id=None,  # Instructor asignado posteriormente por admin
            sede_id=sede_id
        )

        try:
            db.session.add(nuevo_aprendiz)
            db.session.commit()
            flash('Aprendiz registrado con éxito.', 'success')
            return redirect(url_for('adm_sede_bp.gestionar_aprendices'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('adm_sede_bp.registrar_aprendiz'))

    return render_template('adm_sede/registrar_aprendiz.html', now=datetime.now())

# -------------------------------
# Editar Aprendiz
# -------------------------------
@adm_sede_bp.route('/editar_aprendiz/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_sede_required
def editar_aprendiz(id):
    aprendiz = Aprendiz.query.get_or_404(id)
    if aprendiz.sede_id != current_user.sede_id:
        flash('No tienes permiso para editar este aprendiz.', 'danger')
        return redirect(url_for('adm_sede_bp.gestionar_aprendices'))

    if request.method == 'POST':
        nombre = request.form.get('nombre').strip()
        apellido = request.form.get('apellido').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo').strip().lower()
        celular = request.form.get('celular').strip()
        password = request.form.get('password')
        numero_ficha = request.form.get('numero_ficha').strip()
        jornada = request.form.get('jornada')

        logging.info(f"Editando aprendiz id={id}, numero_ficha={numero_ficha}, current_user.sede_id={current_user.sede_id}")

        if not all([nombre, apellido, documento, correo, celular, numero_ficha, jornada]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('adm_sede_bp.editar_aprendiz', id=id))

        try:
            numero_ficha_int = int(numero_ficha)
        except ValueError:
            flash('El número de ficha debe ser un número entero válido.', 'danger')
            return redirect(url_for('adm_sede_bp.editar_aprendiz', id=id))

        # Validar que la ficha exista
        ficha = Ficha.query.filter_by(numero_ficha=numero_ficha_int).first()
        if not ficha:
            logging.error(f"Ficha {numero_ficha_int} no encontrada")
            flash('Error: Ficha no encontrada.', 'danger')
            return redirect(url_for('adm_sede_bp.editar_aprendiz', id=id))

        logging.info(f"Ficha encontrada: id={ficha.id_ficha}, sede_id={ficha.sede_id}")

        # Obtener programa de la ficha
        programa = Programa.query.filter_by(ficha_id=ficha.id_ficha).first()
        if not programa:
            logging.error(f"Programa no encontrado para ficha {ficha.id_ficha}")
            flash('Error: La ficha no tiene un programa asignado.', 'danger')
            return redirect(url_for('adm_sede_bp.editar_aprendiz', id=id))

        logging.info(f"Programa encontrado: id={programa.id_programa}, instructor_id={programa.instructor_id_instructor}")

        # Log current instructor_id before assignment
        logging.info(f"Instructor_id actual del aprendiz: {aprendiz.instructor_id}")
        logging.info(f"Instructor_id del programa: {programa.instructor_id_instructor}")

        # Check sede
        if ficha.sede_id != current_user.sede_id:
            logging.error(f"Ficha sede {ficha.sede_id} != current_user.sede_id {current_user.sede_id}")
            flash('La ficha pertenece a una sede diferente. No puede editar aprendices para esta ficha.', 'danger')
            return redirect(url_for('adm_sede_bp.editar_aprendiz', id=id))

        sede_id = ficha.sede_id
        logging.info(f"Sede_id determinado: {sede_id}")

        # Verificar unicidad
        existing = Aprendiz.query.filter(
            (Aprendiz.documento == documento) | (Aprendiz.correo == correo) | (Aprendiz.celular == celular)
        ).filter(Aprendiz.id_aprendiz != id).first()

        if existing:
            flash('Documento, correo o celular ya están en uso.', 'danger')
            return redirect(url_for('adm_sede_bp.editar_aprendiz', id=id))

        aprendiz.nombre = nombre
        aprendiz.apellido = apellido
        aprendiz.documento = documento
        aprendiz.correo = correo
        aprendiz.celular = celular
        aprendiz.programa_id = programa.id_programa
        aprendiz.sede_id = sede_id
        aprendiz.jornada = jornada
        logging.info(f"Instructor_id mantiene {aprendiz.instructor_id} al cambiar ficha")
        if password:
            aprendiz.password_aprendiz = generate_password_hash(password)

        try:
            db.session.commit()
            flash('Aprendiz actualizado correctamente.', 'success')
            return redirect(url_for('adm_sede_bp.gestionar_aprendices'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('adm_sede/editar_aprendiz.html', aprendiz=aprendiz, now=datetime.now())

# -------------------------------
# Eliminar Aprendiz
# -------------------------------
@adm_sede_bp.route('/eliminar_aprendiz/<int:id>', methods=['POST'])
@login_required
@admin_sede_required
def eliminar_aprendiz(id):
    aprendiz = Aprendiz.query.get_or_404(id)
    if aprendiz.sede_id != current_user.sede_id:
        flash('No tienes permiso para eliminar este aprendiz.', 'danger')
        return redirect(url_for('adm_sede_bp.gestionar_aprendices'))

    try:
        db.session.delete(aprendiz)
        db.session.commit()
        flash('Aprendiz eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar aprendiz: {str(e)}', 'danger')

    return redirect(url_for('adm_sede_bp.gestionar_aprendices'))

# -------------------------------
# Asignar instructor a aprendiz
# -------------------------------
@adm_sede_bp.route('/asignar_instructor/<int:aprendiz_id>', methods=['GET', 'POST'])
@login_required
@admin_sede_required
def asignar_instructor(aprendiz_id):
    aprendiz = Aprendiz.query.get_or_404(aprendiz_id)
    if aprendiz.sede_id != current_user.sede_id:
        flash('No tienes permiso para asignar instructor a este aprendiz.', 'danger')
        return redirect(url_for('adm_sede_bp.dashboard'))

    if request.method == 'POST':
        instructor_id = request.form.get('instructor_id')
        logging.info(f"Asignando instructor a aprendiz id={aprendiz_id}, instructor_id={instructor_id}, current_user.sede_id={current_user.sede_id}")
        logging.info(f"Aprendiz sede_id actual: {aprendiz.sede_id}")
        if instructor_id:
            instructor = Instructor.query.get(int(instructor_id))
            logging.info(f"Instructor encontrado: id={instructor.id_instructor if instructor else None}, sede_id={instructor.sede_id if instructor else None}, admin_sede_id={instructor.administrador_sede_id if instructor else None}")
            if instructor and instructor.administrador_sede_id == current_user.id_admin_sede:
                aprendiz.instructor_id = int(instructor_id)
                # No cambiar sede_id, ya que se determina por la ficha
                logging.info(f"Asignación exitosa: aprendiz.instructor_id={aprendiz.instructor_id}, sede_id permanece {aprendiz.sede_id}")
                db.session.commit()
                flash('Instructor asignado correctamente.', 'success')
            else:
                logging.warning(f"Instructor no válido o no pertenece al admin de sede")
                flash('Instructor no válido.', 'danger')
        else:
            logging.warning(f"No se proporcionó instructor_id")
            flash('No se puede remover el instructor, ya que la sede es obligatoria.', 'danger')
        return redirect(url_for('adm_sede_bp.dashboard'))

    instructores = Instructor.query.filter_by(administrador_sede_id=current_user.id_admin_sede).all()
    return render_template('adm_sede/asignar_instructor.html', aprendiz=aprendiz, instructores=instructores, now=datetime.now())

# -------------------------------
# Editar perfil administrador de sede
# -------------------------------
@adm_sede_bp.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
@admin_sede_required
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
            return redirect(url_for('adm_sede_bp.editar_perfil'))

        # Verificar unicidad
        existing = AdministradorSede.query.filter(
            (AdministradorSede.documento == documento) | (AdministradorSede.correo == correo) | (AdministradorSede.celular == celular)
        ).filter(AdministradorSede.id_admin_sede != current_user.id_admin_sede).first()

        if existing:
            flash('Documento, correo o celular ya están en uso.', 'danger')
            return redirect(url_for('adm_sede_bp.editar_perfil'))

        current_user.nombre = nombre
        current_user.apellido = apellido
        current_user.documento = documento
        current_user.correo = correo
        current_user.celular = celular
        if password:
            current_user.password = generate_password_hash(password)

        try:
            db.session.commit()
            flash('Perfil actualizado correctamente.', 'success')
            return redirect(url_for('adm_sede_bp.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('adm_sede/editar_perfil.html', admin_sede=current_user, now=datetime.now())

# -------------------------------
# Logout administrador de sede
# -------------------------------
@adm_sede_bp.route('/logout')
@login_required
@admin_sede_required
def logout():
    logout_user()
    flash("Has cerrado sesión", "success")
    return redirect(url_for('auth.login'))
