from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.users import Instructor, Aprendiz, TokenInstructor, Notificacion
from app import db
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from datetime import datetime

bp = Blueprint('instructor_bp', __name__, url_prefix='/instructor')


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

    documento = request.args.get('documento')
    query = Aprendiz.query.filter_by(instructor_id=current_user.id_instructor)
    if documento:
        query = query.filter(Aprendiz.documento.like(f"%{documento}%"))
    aprendices_asignados = query.all()

    notificaciones_no_leidas = Notificacion.query.filter(
        Notificacion.rol_destinatario=="Instructor",
        Notificacion.visto==False,
        or_(Notificacion.destinatario_id==current_user.id_instructor, Notificacion.destinatario_id==None)
    ).count()

    eventos = []  # Puedes agregar eventos si los tienes

    return render_template(
        'dasboardh_instructor.html',  # <-- corregido el nombre
        instructor=current_user,
        aprendices=aprendices_asignados,
        documento=documento,
        notificaciones_no_leidas=notificaciones_no_leidas,
        eventos=eventos
    )


# -------------------------------
# Crear nuevo instructor usando token
# -------------------------------
@bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_instructor():
    if request.method == 'POST':
        token_input = request.form.get('token').strip()
        nombre = request.form.get('nombre_instructor').strip()
        apellido = request.form.get('apellido_instructor').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo_instructor').strip().lower()
        celular = request.form.get('celular_instructor').strip()
        password = request.form.get('password_instructor')

        if not all([token_input, nombre, apellido, tipo_documento, documento, correo, celular, password]):
            flash('Todos los campos son obligatorios, incluyendo el token.', 'warning')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        token = TokenInstructor.query.filter_by(token=token_input).first()
        if not token or token.fecha_expiracion < datetime.utcnow() or not token.activo:
            flash('Token inválido, expirado o inactivo.', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        if token.coordinador_id is None:
            flash('El token no tiene un coordinador válido asignado.', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        existe = Instructor.query.filter(
            or_(Instructor.documento == documento,
                Instructor.correo_instructor == correo,
                Instructor.celular_instructor == celular)
        ).first()
        if existe:
            flash('Ya existe un instructor con ese documento, correo o celular.', 'danger')
            return redirect(url_for('instructor_bp.nuevo_instructor'))

        hashed_password = generate_password_hash(password)
        nuevo = Instructor(
            nombre_instructor=nombre,
            apellido_instructor=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            correo_instructor=correo,
            celular_instructor=celular,
            password_instructor=hashed_password,
            coordinador_id=token.coordinador_id
        )

        try:
            db.session.add(nuevo)
            db.session.commit()
            flash('Instructor creado exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el instructor: {str(e)}', 'danger')

    return render_template('instructor.html')


# -------------------------------
# Editar instructor
# -------------------------------
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_instructor(id):
    instructor = Instructor.query.get_or_404(id)
    if request.method == 'POST':
        nombre = request.form.get('nombre_instructor').strip()
        apellido = request.form.get('apellido_instructor').strip()
        tipo_documento = request.form.get('tipo_documento').strip()
        documento = request.form.get('documento').strip()
        correo = request.form.get('correo_instructor').strip().lower()
        celular = request.form.get('celular_instructor').strip()
        password = request.form.get('password_instructor')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('instructor_bp.editar_instructor', id=id))

        instructor.nombre_instructor = nombre
        instructor.apellido_instructor = apellido
        instructor.tipo_documento = tipo_documento
        instructor.documento = documento
        instructor.correo_instructor = correo
        instructor.celular_instructor = celular
        if password:
            instructor.password_instructor = generate_password_hash(password)

        try:
            db.session.commit()
            flash('Instructor actualizado correctamente.', 'success')
            return redirect(url_for('instructor_bp.dashboard_instructor'))
        except IntegrityError:
            db.session.rollback()
            flash('Documento, correo o celular duplicado.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('instructor.html', instructor=instructor, mode='edit')


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
        flash('Instructor eliminado exitosamente.', 'success')
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

    return render_template("perfil_instructor.html", instructor=current_user)


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

    flash(f"Mensaje enviado a {rol_destinatario}", "success")
    return redirect(url_for('instructor_bp.dashboard_instructor'))


# -------------------------------
# Listar notificaciones
# -------------------------------
@bp.route('/notificaciones')
@login_required
def notificaciones():
    lista_notis = Notificacion.query.filter(
        Notificacion.rol_destinatario=="Instructor",
        or_(Notificacion.destinatario_id==current_user.id_instructor, Notificacion.destinatario_id==None)
    ).order_by(Notificacion.fecha_creacion.desc()).all()

    return render_template('notificacion/listar.html', notificaciones=lista_notis)

@bp.route('/notificacion/<int:noti_id>')
@login_required
def ver_notificacion(noti_id):
    noti = Notificacion.query.get_or_404(noti_id)
    # Marcar como visto
    if noti.rol_destinatario == "Instructor" and not noti.visto:
        noti.visto = True
        db.session.commit()
    return render_template('notificacion/ver_notificacion.html', notificacion=noti)

