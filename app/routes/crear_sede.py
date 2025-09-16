from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash
from app import db
from app.models.users import Sede, TokenCoordinador
from flask_login import current_user, login_required

bp = Blueprint('crear_sede_bp', __name__, url_prefix='/crear_sede')

# -----------------------------
# Formulario crear sede
# -----------------------------
@bp.route('/form', methods=['GET'])
@login_required
def formulario_sede():
    return render_template('crear_sede.html', now=datetime.now())

# -----------------------------
# Crear sede
# -----------------------------
@bp.route('/nueva', methods=['POST'])
@login_required
def crear_sede():
    nombre_sede = request.form.get('nombre_sede', "").strip()
    ciudad = request.form.get('ciudad', "").strip()
    token_input = request.form.get('token', "").strip()

    # Validación de campos obligatorios
    if not nombre_sede or not ciudad or not token_input:
        flash("Todos los campos son obligatorios, incluyendo el token.", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    # Verificar que el coordinador no tenga ya sede
    if current_user.sede_id:
        flash("Ya tienes una sede asignada. No puedes crear otra.", "error")
        return redirect(url_for('coordinador_bp.dashboard'))

    # Verificar que la sede no exista (mismo nombre y misma ciudad)
    sede_existente = Sede.query.filter_by(nombre_sede=nombre_sede, ciudad=ciudad).first()
    if sede_existente:
        flash(f"La sede '{nombre_sede}' en la ciudad '{ciudad}' ya existe.", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    # Validar token
    token_obj = TokenCoordinador.query.filter_by(token=token_input).first()
    if not token_obj:
        flash("Token inválido.", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    if not token_obj.usado:
        flash("El token aún no se ha usado para registrar el coordinador.", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    if token_obj.usado_para_sede:
        flash("Este token ya se usó para registrar una sede.", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    # Crear la nueva sede
    nueva_sede = Sede(
        nombre_sede=nombre_sede,
        ciudad=ciudad
    )
    db.session.add(nueva_sede)
    db.session.commit()  # Necesario para obtener id_sede

    # Asignar la sede al coordinador actual
    current_user.sede_id = nueva_sede.id_sede

    # Marcar token como usado para sede
    token_obj.usado_para_sede = True

    # Guardar cambios
    db.session.add(current_user)
    db.session.add(token_obj)
    db.session.commit()

    flash(f"Sede '{nombre_sede}' en '{ciudad}' creada exitosamente y asignada al coordinador.", "success")
    return redirect(url_for('coordinador_bp.dashboard'))
