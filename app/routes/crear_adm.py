from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from app import db
from app.models.users import Administrador
from datetime import datetime

bp = Blueprint('crear_adm', __name__, url_prefix='/crear_adm')

# Define tu clave secreta
CLAVE_SECRETA = "pruebauno"

# --- Paso 1: Verificación de clave ---
@bp.route('/clave', methods=['GET', 'POST'])
def clave():
    if request.method == 'POST':
        clave_ingresada = request.form.get('clave')
        if clave_ingresada == CLAVE_SECRETA:
            session['clave_valida'] = True
            return redirect(url_for('crear_adm.crear_admin'))
        else:
            flash("Clave incorrecta.", "danger")
            return render_template("clave.html", now=datetime.now())
    return render_template("clave.html", now=datetime.now())


# --- Paso 2: Formulario de creación de admin ---
@bp.route('/crear_admin', methods=['GET', 'POST'])
def crear_admin():
    # Verificar que la clave fue validada
    if not session.get('clave_valida'):
        flash("Debes ingresar la clave primero.", "warning")
        return redirect(url_for('crear_adm.clave'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        documento = request.form.get('documento')
        password = request.form.get('password')

        if not all([nombre, apellido, documento, password]):
            flash("Todos los campos son obligatorios.", "warning")
            return render_template("crear_admin.html", now=datetime.now())

        hashed_password = generate_password_hash(password)
        nuevo_admin = Administrador(
            nombre=nombre,
            apellido=apellido,
            documento=documento,
            password=hashed_password
        )

        try:
            db.session.add(nuevo_admin)
            db.session.commit()
            session.pop('clave_valida')  # Limpiar la sesión
            flash("Administrador creado exitosamente.", "success")

            # Renderizamos el mismo template para que el modal se muestre
            # y le pasamos la URL de redirección
            return render_template("crear_admin.html", now=datetime.now(), redirect_url=url_for("auth.login"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear el administrador: {str(e)}", "danger")
            return render_template("crear_admin.html", now=datetime.now())

    return render_template("crear_admin.html", now=datetime.now())

