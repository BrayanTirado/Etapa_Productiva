from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from app.models.users import Coordinador, Instructor, Aprendiz, TokenInstructor, TokenCoordinador, Programa, Notificacion, Sede
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
# Registro inicial del coordinador
# -------------------------------
@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        token_input = request.form.get('token')
        token_obj = TokenCoordinador.query.filter_by(token=token_input, usado=False).first()
        if not token_obj:
            flash("Token inválido o ya usado", "error")
            return render_template('coordinador/registro.html')

        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        correo = request.form.get('correo')
        celular = request.form.get('celular')
        password = request.form.get('password')

        if not all([nombre, apellido, tipo_documento, documento, correo, celular, password]):
            flash("Todos los campos son obligatorios", "error")
            return render_template('coordinador/registro.html')

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
            flash("Registro exitoso. Ahora inicia sesión", "success")
            return redirect(url_for('coordinador_bp.login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Ocurrió un error al registrar: {str(e)}", "error")
            return render_template('coordinador/registro.html')

    return render_template('coordinador/registro.html')

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
            return render_template('coordinador/login.html')

        login_user(coordinador)
        return redirect(url_for('coordinador_bp.dashboard'))

    return render_template('login.html')

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
    instructores = Instructor.query.filter_by(coordinador_id=current_user.id_coordinador).all()
    aprendices = Aprendiz.query.join(Instructor).filter(Instructor.coordinador_id == current_user.id_coordinador).all()
    tokens = TokenInstructor.query.filter_by(coordinador_id=current_user.id_coordinador).all()

    # Contar notificaciones no leídas (rol o destinatario específico)
    notificaciones_no_leidas = Notificacion.query.filter(
        Notificacion.rol_destinatario=="Coordinador",
        Notificacion.visto==False,
        or_(Notificacion.destinatario_id==current_user.id_coordinador, Notificacion.destinatario_id==None)
    ).count()

    # Para enviar mensajes: lista de usuarios disponibles
    usuarios = Instructor.query.filter_by(coordinador_id=current_user.id_coordinador).all() + \
               Aprendiz.query.join(Instructor).filter(Instructor.coordinador_id == current_user.id_coordinador).all()

    return render_template(
        'coordinador/dashboard_coordinador.html',
        instructores=instructores,
        aprendices=aprendices,
        tokens=tokens,
        notificaciones_no_leidas=notificaciones_no_leidas,
        usuarios=usuarios
    )

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

        # Enviar notificación a instructores (rol)
        enviar_notificacion(
            mensaje=f"Se ha generado un nuevo token para instructores: {token_str}",
            rol_destinatario="Instructor"
        )

        return redirect(url_for('coordinador_bp.dashboard'))

    return render_template('coordinador/generar_token.html')

# -------------------------------
# Asignar aprendices a instructores
# -------------------------------
@bp.route('/asignar_aprendiz', methods=['GET', 'POST'])
@login_required
@coordinador_required
def asignar_aprendiz():
    instructores = Instructor.query.all()
    aprendices = []
    programa = None
    ficha = request.args.get("ficha")

    if ficha:
        programa = Programa.query.filter_by(ficha=ficha).first()
        if programa:
            aprendices = Aprendiz.query.filter_by(programa_id=programa.id_programa).all()
    else:
        aprendices = Aprendiz.query.all()

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

                # Notificación al instructor asignado
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
        instructores=instructores,
        programa=programa
    )

# -------------------------------
# Enviar mensaje a un rol
# -------------------------------
@bp.route('/enviar_mensaje', methods=['GET', 'POST'])
@login_required
@coordinador_required
def enviar_mensaje():
    roles_disponibles = ["Administrador", "Instructor", "Aprendiz"]

    if request.method == 'POST':
        rol_destinatario = request.form.get('rol_destinatario')
        motivo = request.form.get('motivo')
        mensaje = request.form.get('mensaje')

        # Validaciones
        if not rol_destinatario or rol_destinatario not in roles_disponibles:
            flash("Debes seleccionar un rol válido", "error")
            return render_template('coordinador/enviar_mensaje.html', roles=roles_disponibles)

        if not mensaje or mensaje.strip() == "":
            flash("El mensaje no puede estar vacío", "error")
            return render_template('coordinador/enviar_mensaje.html', roles=roles_disponibles)

        # Guardar notificación
        noti = Notificacion(
            mensaje=f"[{motivo}] {mensaje}",
            remitente_id=current_user.id_coordinador,
            rol_remitente="Coordinador",
            rol_destinatario=rol_destinatario,
            visto=False
        )
        db.session.add(noti)
        db.session.commit()

        flash(f"Mensaje enviado al rol {rol_destinatario}", "success")
        return redirect(url_for('coordinador_bp.dashboard'))

    return render_template('coordinador/enviar_mensaje.html', roles=roles_disponibles)

# -------------------------------
# Listar notificaciones del coordinador
# -------------------------------
@bp.route('/notificaciones')
@login_required
@coordinador_required
def notificaciones():
    lista_notis = Notificacion.query.filter(
        Notificacion.rol_destinatario=="Coordinador",
        or_(Notificacion.destinatario_id==current_user.id_coordinador, Notificacion.destinatario_id==None)
    ).order_by(Notificacion.fecha_creacion.desc()).all()

    return render_template('notificacion/listar.html', notificaciones=lista_notis)

# -------------------------------
# Marcar notificación como vista
# -------------------------------
@bp.route('/notificacion/<int:noti_id>')
@login_required  # <- solo login_required, no coordinador_required
def ver_notificacion(noti_id):
    noti = Notificacion.query.get_or_404(noti_id)
    noti.visto = True
    db.session.commit()
    return render_template('notificacion/ver_notificacion.html', notificacion=noti)

@bp.route('/crear_sede', methods=['GET', 'POST'])
@login_required
@coordinador_required
def crear_sede():
    if request.method == 'POST':
        # Obtener datos del formulario
        token_input = request.form.get('token')  # campo token
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')

        # Validar que los campos obligatorios estén completos
        if not all([token_input, nombre, direccion]):
            flash("Token, nombre y dirección son obligatorios", "error")
            return render_template('crear_sede.html')

        # Validar token
        from app.models.users import TokenCoordinador, Sede  # asegurar importaciones
        token_obj = TokenCoordinador.query.filter_by(token=token_input, usado=False).first()
        if not token_obj:
            flash("Token inválido o ya usado", "error")
            return render_template('crear_sede.html')

        # Crear la sede
        sede = Sede(
            nombre=nombre,
            direccion=direccion,
            correo=correo,
            telefono=telefono,
            coordinador_id=current_user.id_coordinador
        )

        try:
            db.session.add(sede)
            token_obj.usado = True  # marcar token como usado
            db.session.commit()
            flash("Sede registrada exitosamente", "success")
            return redirect(url_for('coordinador_bp.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Ocurrió un error al registrar la sede: {str(e)}", "error")
            return render_template('crear_sede.html')

    return render_template('crear_sede.html')

