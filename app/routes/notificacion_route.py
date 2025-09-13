from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.users import Notificacion
from datetime import datetime

notificacion_bp = Blueprint('notificacion_bp', __name__, url_prefix='/notificacion')

# Crear una notificación
@notificacion_bp.route('/crear', methods=['POST'])
@login_required
def crear_notificacion():
    mensaje = request.form.get('mensaje', '').strip()
    destinatario_id = request.form.get('destinatario_id', type=int)
    rol_destinatario = request.form.get('rol_destinatario')

    if not mensaje:
        flash("El mensaje no puede estar vacío.", "warning")
        return redirect(request.referrer)

    noti = Notificacion(
        mensaje=mensaje,
        remitente_id=current_user.id,
        destinatario_id=destinatario_id if destinatario_id else None,
        rol_destinatario=rol_destinatario if rol_destinatario else None
    )
    db.session.add(noti)
    db.session.commit()
    flash("Notificación enviada correctamente ✅", "success")
    return redirect(request.referrer)

# Listar notificaciones del usuario
@notificacion_bp.route('/listar')
@login_required
def listar_notificaciones():
    # Notificaciones directas al usuario o al rol del usuario
    notificaciones = Notificacion.query.filter(
        (Notificacion.destinatario_id == current_user.id) |
        (Notificacion.rol_destinatario == current_user.__class__.__name__)
    ).order_by(Notificacion.fecha_creacion.desc()).all()
    return render_template('notificacion/listar.html', notificaciones=notificaciones, now=datetime.now())

# Marcar notificación como vista
@notificacion_bp.route('/marcar/<int:id>')
@login_required
def marcar_visto(id):
    noti = Notificacion.query.get_or_404(id)
    if noti.destinatario_id == current_user.id or noti.rol_destinatario == current_user.__class__.__name__:
        noti.visto = True
        db.session.commit()
        flash("Notificación marcada como leída.", "success")
    return redirect(request.referrer or url_for('notificacion_bp.listar_notificaciones'))
