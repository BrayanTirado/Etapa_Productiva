from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.users import Instructor, Aprendiz, TokenInstructor, Notificacion, Coordinador, Administrador, Contrato, Programa, Sede
from app import db
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from datetime import datetime, date 

bp = Blueprint('instructor_bp', __name__, url_prefix='/instructor')

bp.route('/aprendiz/<int:aprendiz_id>/progreso')
@login_required
def ver_progreso_aprendiz(aprendiz_id):
    # Buscar el aprendiz
    aprendiz = Aprendiz.query.get_or_404(aprendiz_id)

    # Verificar que el usuario sea instructor y tenga asignado a este aprendiz
    if not hasattr(current_user, "id_instructor") or aprendiz.instructor_id != current_user.id:
        flash("No tienes permiso para ver este aprendiz.", "error")
        return redirect(url_for('instructor_bp.dashboard_instructor'))

    # Renderizar la plantilla con los datos del aprendiz
    return render_template('ver_progreso_aprendiz.html', aprendiz=aprendiz)
# -------------------------------
# Función para enviar notificación
# -------------------------------
def enviar_notificacion(mensaje, destinatario_id=None, rol_destinatario=None):
    noti = Notificacion(
        mensaje=mensaje,
        remitente_id=current_user.id_instructor,
        rol_remitente="Instructor",
        destinatario_id=destinatario_id,
        rol_destinatario=rol_destinatario,
        visto=False
    )
    db.session.add(noti)
    db.session.commit()


# -------------------------------
# Dashboard del instructor
# -------------------------------
@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard_instructor():
    if not hasattr(current_user, "id_instructor"):
        flash("Acceso denegado", "error")
        return redirect(url_for('auth.dashboard'))

    sede_id = current_user.sede_id  # ✅ sede del instructor

    # ✅ Filtrar aprendices asignados SOLO en la misma sede
    documento = request.args.get('documento')
    query = Aprendiz.query.filter_by(instructor_id=current_user.id_instructor, sede_id=sede_id)
    if documento:
        query = query.filter(Aprendiz.documento.like(f"%{documento}%"))
    aprendices_asignados = query.all()

    # ✅ Coordinadores SOLO de la misma sede
    coordinadores = Coordinador.query.filter_by(sede_id=sede_id).all()

    # ✅ Administradores (estos pueden ser globales, los dejo sin sede, pero si quieres, también filtras por sede_id)
    administradores = Administrador.query.all()

    # ✅ Notificaciones no leídas SOLO del instructor actual
    notificaciones_no_leidas = Notificacion.query.filter(
        Notificacion.rol_destinatario == "Instructor",
        Notificacion.visto == False,
        Notificacion.destinatario_id == current_user.id_instructor
    ).count()

    # ✅ Aprendices que finalizan para armar eventos (SOLO de la misma sede)
    aprendices_finalizan = (
        db.session.query(Aprendiz, Contrato, Programa)
        .join(Contrato, Aprendiz.contrato_id == Contrato.id_contrato)
        .join(Programa, Aprendiz.programa_id == Programa.id_programa)
        .filter(Contrato.fecha_fin.isnot(None))
        .filter(Aprendiz.sede_id == sede_id)  # 🔑 Filtrar por sede del instructor
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
        aprendices=aprendices_asignados,
        coordinadores=coordinadores,
        administradores=administradores,
        documento=documento,
        notificaciones_no_leidas=notificaciones_no_leidas,
        eventos=eventos,
        now=datetime.now()
    )


# -------------------------------
# Crear nuevo instructor usando token
# -------------------------------
@bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_instructor():
    from app.models.users import Sede  # Importar Sede aquí
    if request.method == 'POST':
        token_input = request.form.get('token').strip()
        nombre = request.form.get('nombre_instructor').strip()
        apellido = request.form.get('apellido_instructor').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo_instructor').strip().lower()
        celular = request.form.get('celular_instructor').strip()
        password = request.form.get('password_instructor')
        sede_nombre = request.form.get('sede_id')

        if not all([token_input, nombre, apellido, tipo_documento, documento, correo, celular, password, sede_nombre]):
            flash('Todos los campos son obligatorios, incluyendo el token.', 'warning')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        # Buscar la sede por nombre
        sede = Sede.query.filter_by(nombre_sede=sede_nombre).first()
        if not sede:
            flash('La sede seleccionada no existe en el sistema.', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        # ✅ Validar token
        token = TokenInstructor.query.filter_by(token=token_input).first()
        if not token or token.fecha_expiracion < datetime.utcnow() or not token.activo:
            flash('Token inválido, expirado o inactivo.', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        if token.coordinador_id is None or token.sede_id is None:
            flash('El token no tiene un coordinador o sede válidos asignados.', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        # ✅ Validar duplicados globales (todos los tipos de usuario)
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
            flash('Ya existe un usuario con ese documento.', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        if email_existe:
            flash('Ya existe un usuario con ese email.', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        if celular_existe:
            flash('Ya existe un usuario con ese número de celular.', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        # ✅ Crear instructor con la sede_id heredada del token
        hashed_password = generate_password_hash(password)

        # 🔎 Debug 1: valores que vienen del token
        print("DEBUG TOKEN:",
              "id_token:", token.id_token,
              "coordinador_id:", token.coordinador_id,
              "sede_id:", token.sede_id)

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

        # 🔎 Debug 2: antes del commit
        print("DEBUG NUEVO INSTRUCTOR (antes de commit):",
              "nombre:", nuevo.nombre_instructor,
              "coordinador_id:", nuevo.coordinador_id,
              "sede_id:", nuevo.sede_id)

        try:
            db.session.add(nuevo)
            db.session.commit()

            # 🔎 Debug 3: después del commit
            print("DEBUG INSTRUCTOR GUARDADO:",
                  "id_instructor:", nuevo.id_instructor,
                  "coordinador_id:", nuevo.coordinador_id,
                  "sede_id:", nuevo.sede_id)

            flash('Instructor creado exitosamente. Ahora puedes iniciar sesión.', 'modal')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el instructor: {str(e)}', 'danger')

    # Mostrar TODAS las sedes disponibles para que el instructor pueda elegir
    sedes = Sede.query.all()
    return render_template('instructor.html', sedes=sedes)

# -------------------------------
# Editar instructor
# -------------------------------
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_instructor(id):
    from app.models.users import Sede  # Importar Sede aquí
    instructor = Instructor.query.get_or_404(id)
    if request.method == 'POST':
        nombre = request.form.get('nombre_instructor').strip()
        apellido = request.form.get('apellido_instructor').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo_instructor').strip().lower()
        celular = request.form.get('celular_instructor').strip()
        password = request.form.get('password_instructor')
        sede_nombre = request.form.get('sede_id')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular, sede_nombre]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('instructor_bp.editar_instructor', id=id))

        # Buscar la sede por nombre
        sede = Sede.query.filter_by(nombre_sede=sede_nombre).first()
        if not sede:
            flash('La sede seleccionada no existe en el sistema.', 'danger')
            return redirect(url_for('instructor_bp.editar_instructor', id=id))

        instructor.nombre_instructor = nombre
        instructor.apellido_instructor = apellido
        instructor.tipo_documento = tipo_documento
        instructor.documento = documento
        instructor.correo_instructor = correo
        instructor.celular_instructor = celular
        instructor.sede_id = sede.id_sede
        if password:
            instructor.password_instructor = generate_password_hash(password)

        try:
            db.session.commit()
            flash('Instructor actualizado correctamente.', 'modal')
            return redirect(url_for('instructor_bp.dashboard_instructor'))
        except IntegrityError:
            db.session.rollback()
            flash('Documento, correo o celular duplicado.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    sedes = Sede.query.all()
    return render_template('instructor.html', instructor=instructor, mode='edit', sedes=sedes, now=datetime.now())


# -------------------------------
# Eliminar instructor
# -------------------------------
@bp.route('/eliminar/<int:id>')
@login_required
def eliminar_instructor(id):
    instructor = Instructor.query.get_or_404(id)
    try:
        db.session.delete(instructor)
        db.session.commit()
        flash('Instructor eliminado exitosamente.', 'modal')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar instructor: {str(e)}', 'danger')
    return redirect(url_for('auth.login'))


# -------------------------------
# Perfil del instructor
# -------------------------------
@bp.route('/perfil')
@login_required
def perfil_instructor():
    if not hasattr(current_user, "id_instructor"):
        flash("No tienes permiso para acceder a este perfil.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("perfil_instructor.html", instructor=current_user, now=datetime.now())


# -------------------------------
# Enviar mensaje
# -------------------------------
@bp.route('/enviar_mensaje', methods=['POST'])
@login_required
def enviar_mensaje():
    rol_destinatario = request.form.get('rol_destinatario')
    destinatario_id = request.form.get('destinatario_id')  # opcional
    mensaje = request.form.get('mensaje')

    if not rol_destinatario or not mensaje:
        flash("Debes seleccionar destinatario y escribir un mensaje", "error")
        return redirect(url_for('instructor_bp.dashboard_instructor'))

    enviar_notificacion(
        mensaje=mensaje,
        destinatario_id=destinatario_id if destinatario_id else None,
        rol_destinatario=rol_destinatario
    )

    flash(f"Mensaje enviado a {rol_destinatario}", "modal")
    return redirect(url_for('instructor_bp.dashboard_instructor'))


# -------------------------------
# Listar notificaciones
# -------------------------------
@bp.route('/notificaciones')
@login_required
def notificaciones():
    # Página actual desde la query string
    pagina = request.args.get('pagina', 1, type=int)
    per_page = 10  # Notificaciones por página

    # Query filtrando por instructor
    pagination = Notificacion.query.filter(
        Notificacion.rol_destinatario == "Instructor",
        or_(Notificacion.destinatario_id == current_user.id_instructor, Notificacion.destinatario_id == None)
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
from datetime import timedelta

@bp.route('/notificacion/<int:noti_id>')
@login_required
def ver_notificacion(noti_id):
    noti = Notificacion.query.get_or_404(noti_id)
    
    # Marcar como visto
    if noti.rol_destinatario == "Instructor" and not noti.visto:
        noti.visto = True
        db.session.commit()

    # Obtener nombre del remitente (puedes usar tu función obtener_remitente si la tienes)
    remitente_nombre = f"{noti.remitente_id}"  # ajusta según tu función
    
    # Calcular fecha_local (hora local)
    fecha_local = noti.fecha_creacion - timedelta(hours=5)  # ajustar según tu zona horaria

    return render_template(
        'notificacion/ver_notificacion.html',
        notificacion=noti,
        remitente_nombre=remitente_nombre,
        now=datetime.now(),
        fecha_local=fecha_local
    )


# Responder notificación (Instructor)
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
            flash('Respuesta enviada con éxito.', 'modal')
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
    if current_user.__class__.__name__ != "Instructor":
        return "", 400

    user_id = current_user.id_instructor
    rol = "Instructor"

    # Marcar todas las notificaciones como vistas
    Notificacion.query.filter(
        Notificacion.destinatario_id == user_id,
        Notificacion.rol_destinatario == rol,
        Notificacion.visto == False
    ).update({ "visto": True }, synchronize_session=False)

    db.session.commit()
    return "", 200

