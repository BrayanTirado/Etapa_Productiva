from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash
from app import db
from app.models.users import Sede
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

    # Validación de campos obligatorios
    if not nombre_sede or not ciudad:
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    # Verificar que la sede no exista (mismo nombre y misma ciudad)
    sede_existente = Sede.query.filter_by(nombre_sede=nombre_sede, ciudad=ciudad).first()
    if sede_existente:
        flash(f"La sede '{nombre_sede}' en la ciudad '{ciudad}' ya existe.", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    # Crear la nueva sede
    nueva_sede = Sede(
        nombre_sede=nombre_sede,
        ciudad=ciudad
    )
    db.session.add(nueva_sede)
    db.session.commit()

    flash(f"Sede '{nombre_sede}' en '{ciudad}' creada exitosamente.", "success")
    return redirect(url_for('adm_bp.dashboard'))
