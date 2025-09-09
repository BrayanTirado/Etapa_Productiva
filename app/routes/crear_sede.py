from datetime import datetime
import secrets
from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from app import db
from app.models.users import Sede, TokenCoordinador
from flask_login import current_user, login_required

bp = Blueprint('crear_sede_bp', __name__, url_prefix='/crear_sede')

# Clave secreta para acceso inicial al formulario (opcional)
CLAVE_SECRETA = "PruebaUno"

# -----------------------------
# Página de acceso con clave
# -----------------------------
@bp.route('/', methods=['GET', 'POST'])
def acceso_formulario():
    if request.method == 'POST':
        clave = request.form.get('clave')
        if clave != CLAVE_SECRETA:
            flash("Clave incorrecta", "error")
            return render_template('clave_secreta.html')
        session['autorizado'] = True
        return redirect(url_for('crear_sede_bp.formulario_sede'))
    return render_template('clave_secreta.html')


# -----------------------------
# Formulario crear sede
# -----------------------------
@bp.route('/form', methods=['GET'])
@login_required
def formulario_sede():
    if not session.get('autorizado'):
        flash("Acceso no autorizado", "error")
        return redirect(url_for('crear_sede_bp.acceso_formulario'))
    return render_template('crear_sede.html')


# -----------------------------
# Crear sede
# -----------------------------
@bp.route('/nueva', methods=['POST'])
@login_required
def crear_sede():
    if not session.get('autorizado'):
        flash("Acceso no autorizado", "error")
        return redirect(url_for('crear_sede_bp.acceso_formulario'))

    nombre = request.form.get('nombre')
    ciudad = request.form.get('direccion')
    token_input = request.form.get('token')

    if not nombre or not ciudad or not token_input:
        flash("Todos los campos son obligatorios, incluyendo el token", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    # Verificar que la sede no exista
    if Sede.query.filter_by(nombre=nombre).first():
        flash(f"La sede '{nombre}' ya existe.", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    # Validar token de coordinador generado por admin
    token_obj = TokenCoordinador.query.filter_by(token=token_input).first()
    if not token_obj:
        flash("Token inválido", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    if not token_obj.usado:
        flash("El token aún no se ha usado para registrar el coordinador", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    if token_obj.usado_para_sede:
        flash("Este token ya se ha usado para registrar una sede", "error")
        return redirect(url_for('crear_sede_bp.formulario_sede'))

    # Registrar la sede
    nueva_sede = Sede(
    nombre=nombre,
    ciudad=ciudad
)
    db.session.add(nueva_sede)

    # Marcar token como usado para sede
    token_obj.usado_para_sede = True

    db.session.commit()

    flash(f"Sede '{nombre}' creada con éxito.", "success")
    session.pop('autorizado', None)
    return redirect(url_for('coordinador_bp.dashboard'))
