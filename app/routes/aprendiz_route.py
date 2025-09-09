from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.users import Aprendiz, Evidencia, Programa, Instructor, Coordinador, Administrador, Notificacion, Contrato
from app import db
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date

# Blueprint para todas las rutas relacionadas con Aprendiz
bp = Blueprint('aprendiz_bp', __name__, url_prefix='/aprendiz')


# -------------------------------
# CREAR NUEVO APRENDIZ
# -------------------------------
@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_aprendiz():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        email = request.form.get('email')
        celular = request.form.get('celular')
        password_aprendiz = request.form.get('password_aprendiz')

        ficha_input = request.form.get('ficha')
        nombre_programa_input = request.form.get('nombre_programa')
        jornada_input = request.form.get('jornada')

        if not all([nombre, apellido, tipo_documento, documento, email, celular, password_aprendiz,
                    ficha_input, nombre_programa_input, jornada_input]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('aprendiz_bp.nuevo_aprendiz'))

        programa = Programa.query.filter_by(
            ficha=ficha_input,
            nombre_programa=nombre_programa_input,
            jornada=jornada_input
        ).first()

        if not programa:
            programa = Programa(ficha=ficha_input, nombre_programa=nombre_programa_input, jornada=jornada_input)
            db.session.add(programa)
            db.session.commit()

        hashed_password = generate_password_hash(password_aprendiz)
        nuevo = Aprendiz(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            email=email,
            celular=celular,
            password_aprendiz=hashed_password,
            programa_id=programa.id_programa
        )

        try:
            db.session.add(nuevo)
            db.session.commit()
            flash('Aprendiz creado exitosamente.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un aprendiz con ese documento, correo o celular.', 'danger')
            return redirect(url_for('aprendiz_bp.nuevo_aprendiz'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el aprendiz: {str(e)}', 'danger')
            return redirect(url_for('aprendiz_bp.nuevo_aprendiz'))

    return render_template('aprendiz/nuevo.html')


# -------------------------------
# EDITAR APRENDIZ
# -------------------------------
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_aprendiz(id):
    aprendiz = Aprendiz.query.get_or_404(id)

    if not (hasattr(current_user, 'id_aprendiz') and current_user.id_aprendiz == id) and not hasattr(current_user, 'id_instructor'):
        flash('No tienes permiso para editar este perfil.', 'danger')
        return redirect(url_for('auth.dashboard'))

    tipos_documento = [
        'Cedula de Ciudadania',
        'Tarjeta de Identidad',
        'Cedula Extrangera',
        'Registro Civil'
    ]

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento', '').strip()
        email = request.form.get('email', '').strip()
        celular = request.form.get('celular', '').strip()
        password_aprendiz = request.form.get('password_aprendiz', '').strip()

        if not all([nombre, apellido, tipo_documento, documento, email, celular]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

        if tipo_documento not in tipos_documento:
            flash('Valor de tipo de documento inválido.', 'danger')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

        aprendiz.nombre = nombre
        aprendiz.apellido = apellido
        aprendiz.tipo_documento = tipo_documento
        aprendiz.documento = documento
        aprendiz.email = email
        aprendiz.celular = celular

        if password_aprendiz:
            aprendiz.password_aprendiz = generate_password_hash(password_aprendiz)

        try:
            db.session.commit()
            flash('Aprendiz actualizado correctamente.', 'success')
            return redirect(url_for('aprendiz_bp.perfil', id=id if hasattr(current_user, 'id_instructor') else None))
        except IntegrityError:
            db.session.rollback()
            flash('Documento, email o celular duplicado.', 'danger')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

    return render_template(
        'perfil_aprendiz.html',
        aprendiz=aprendiz,
        mode='edit',
        tipos_documento=tipos_documento,
        es_aprendiz=(hasattr(current_user, 'id_aprendiz') and current_user.id_aprendiz == id),
        aprendiz_id=id if hasattr(current_user, 'id_instructor') else None
    )


@bp.route('/dasboardh/<int:aprendiz_id>')
@login_required
def dasboardh_aprendiz(aprendiz_id):
    aprendiz = Aprendiz.query.get_or_404(aprendiz_id)
    contrato = aprendiz.contrato

    # --- Progreso de evidencias ---
    total_requerido = 17  # ⚠️ ajusta según tus reglas
    evidencias_subidas = len(aprendiz.evidencias)
    progreso = int((evidencias_subidas / total_requerido) * 100) if total_requerido > 0 else 0

    # --- Progreso en tiempo ---
    progreso_tiempo = 0
    if contrato and contrato.fecha_inicio and contrato.fecha_fin:
        fecha_inicio = contrato.fecha_inicio.date() if hasattr(contrato.fecha_inicio, "date") else contrato.fecha_inicio
        fecha_fin = contrato.fecha_fin.date() if hasattr(contrato.fecha_fin, "date") else contrato.fecha_fin
        total_dias = (fecha_fin - fecha_inicio).days
        dias_transcurridos = (date.today() - fecha_inicio).days
        if total_dias > 0:
            progreso_tiempo = round((dias_transcurridos / total_dias) * 100, 2)
            progreso_tiempo = min(max(progreso_tiempo, 0), 100)
                # --- Contar notificaciones no leídas ---
    notificaciones_no_leidas = Notificacion.query.filter_by(
        destinatario_id=aprendiz.id_aprendiz,
        visto=False
    ).count()

    return render_template(
        "dasboardh_aprendiz.html",
        aprendiz=aprendiz,
        contrato=contrato,
        progreso=progreso,
        progreso_tiempo=progreso_tiempo,
        ocultar_notificaciones=False,
        notificaciones_no_leidas=notificaciones_no_leidas

    )

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
# Enviar mensaje desde el dashboard
# -------------------------------
@bp.route('/enviar_mensaje', methods=['POST'])
@login_required
def enviar_mensaje():
    if not hasattr(current_user, 'id_aprendiz'):
        flash("No tienes permisos para enviar mensajes.", "danger")
        return redirect(url_for("auth.dashboard"))

    roles_disponibles = ["Administrador", "Coordinador", "Instructor"]

    # Leer valores del formulario
    rol_destinatario = request.form.get("rol_destinatario")
    motivo = request.form.get("motivo")
    mensaje = request.form.get("mensaje")

    # Validaciones
    if not rol_destinatario or rol_destinatario not in roles_disponibles:
        flash("Debes seleccionar un rol válido.", "warning")
    elif not mensaje or not mensaje.strip():
        flash("El mensaje no puede estar vacío.", "warning")
    else:
        noti = Notificacion(
            mensaje=f"[{motivo}] {mensaje}",
            remitente_id=current_user.id_aprendiz,
            rol_remitente="Aprendiz",
            rol_destinatario=rol_destinatario,
            visto=False
        )
        db.session.add(noti)
        db.session.commit()
        flash(f"✅ Mensaje enviado al rol {rol_destinatario}", "success")

    # Redirigir al dashboard del aprendiz para limpiar el formulario
    return redirect(url_for('aprendiz_bp.dasboardh_aprendiz', aprendiz_id=current_user.id_aprendiz))

# -------------------------------
# Listar notificaciones
# -------------------------------
@bp.route('/notificaciones')
@login_required
def notificaciones():
    if not hasattr(current_user, 'id_aprendiz'):
        flash("No tienes permisos para esta sección.", "danger")
        return redirect(url_for("auth.dashboard"))

    lista_notis = Notificacion.query.filter(
        Notificacion.rol_destinatario == "Aprendiz",
        (Notificacion.destinatario_id == current_user.id_aprendiz) | (Notificacion.destinatario_id == None)
    ).order_by(Notificacion.fecha_creacion.desc()).all()

    return render_template('notificacion/listar.html', notificaciones=lista_notis)


# -------------------------------
# Marcar notificación como vista
# -------------------------------
@bp.route('/notificacion/ver/<int:noti_id>')
@login_required
def ver_notificacion(noti_id):
    noti = Notificacion.query.get_or_404(noti_id)

    # Validar que el aprendiz sea remitente o destinatario
    if not (
        hasattr(current_user, 'id_aprendiz') and
        (noti.remitente_id == current_user.id_aprendiz or noti.destinatario_id == current_user.id_aprendiz)
    ):
        flash("No tienes permiso para ver esta notificación.", "danger")
        return redirect(url_for("aprendiz_bp.notificaciones"))

    noti.visto = True
    db.session.commit()

    return render_template('notificacion/ver_notificacion.html', notificacion=noti)

# -------------------------------
# PERFIL APRENDIZ
# -------------------------------
@bp.route('/perfil/<int:id>', methods=['GET'])
@login_required
def perfil(id):
    aprendiz = Aprendiz.query.get_or_404(id)
    return render_template('perfil_aprendiz.html', aprendiz=aprendiz)
