from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models.users import Administrador, TokenCoordinador, Notificacion
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
    noti = Notificacion(
        mensaje=mensaje,
        remitente_id=current_user.id_admin,
        rol_remitente="Administrador",
        destinatario_id=destinatario_id,
        rol_destinatario=rol_destinatario,
        visto=False
    )
    db.session.add(noti)
    db.session.commit()

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
            return render_template('adm/login.html')
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
    return render_template(
        'adm/dashboard_adm.html',
        tokens=tokens,
        notificaciones_no_leidas=notificaciones_no_leidas
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
# Enviar mensaje a un rol
# -------------------------------
@adm_bp.route('/enviar_mensaje', methods=['GET', 'POST'])
@login_required
@admin_required
def enviar_mensaje():
    roles_disponibles = ["Coordinador", "Instructor", "Aprendiz"]

    if request.method == 'POST':
        rol_destinatario = request.form.get('rol_destinatario')
        motivo = request.form.get('motivo')
        mensaje = request.form.get('mensaje')

        if not rol_destinatario or rol_destinatario not in roles_disponibles:
            flash("Debes seleccionar un rol válido", "error")
            return render_template('adm/enviar_mensaje.html', roles=roles_disponibles)

        if not mensaje or mensaje.strip() == "":
            flash("El mensaje no puede estar vacío", "error")
            return render_template('adm/enviar_mensaje.html', roles=roles_disponibles)

        noti = Notificacion(
            mensaje=f"[{motivo}] {mensaje}",
            remitente_id=current_user.id_admin,
            rol_remitente="Administrador",
            rol_destinatario=rol_destinatario,
            visto=False
        )
        db.session.add(noti)
        db.session.commit()
        flash(f"Mensaje enviado al rol {rol_destinatario}", "success")
        return redirect(url_for('adm_bp.dashboard'))

    return render_template('adm/enviar_mensaje.html', roles=roles_disponibles)

# -------------------------------
# Listar notificaciones
# -------------------------------
@adm_bp.route('/notificaciones')
@login_required
@admin_required
def notificaciones():
    lista_notis = Notificacion.query.filter_by(
        rol_destinatario="Administrador"
    ).order_by(Notificacion.fecha_creacion.desc()).all()
    return render_template('notificacion/listar.html', notificaciones=lista_notis)

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
    return render_template('notificacion/ver_notificacion.html', notificacion=noti)



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
