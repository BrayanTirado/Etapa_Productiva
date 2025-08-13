from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.users import Users
from app import db

# Blueprint para autenticación
bp = Blueprint('auth', __name__, url_prefix='/auth')


# --- LOGIN ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está autenticado, redirige al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        nameUser = request.form['nameUser']
        passwordUser = request.form['passwordUser']

        user = Users.query.filter_by(nameUser=nameUser).first()

        if user and check_password_hash(user.passwordUser, passwordUser):
            login_user(user)
            flash("Inicio de sesión exitoso", "success")
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Credenciales inválidas. Intenta de nuevo.', 'danger')

    return render_template("login.html")


# --- DASHBOARD POR ROL ---
@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rolUser == 'Coordinador':
        return render_template('coordinador.html', fichas_total=10, solicitudes_pendientes=5, instructores_activos=8)
    elif current_user.rolUser == 'Instructor':
        return render_template('instructor.html', fichas_asignadas=4, programas_total=2, mensajes_nuevos=1)
    elif current_user.rolUser == 'Admin':
        return render_template('admin.html', total_usuarios=50, total_bd=3, accesos_ultimos=12)
    else:
        return "No tienes permiso para ver este panel", 403


# --- LOGOUT ---
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


# --- REGISTRO DE USUARIO ---
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nameUser = request.form['nameUser']
        passwordUser = request.form['passwordUser']
        rolUser = request.form['rolUser']

        # Validación básica
        if not nameUser or not passwordUser or not rolUser:
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('auth.register'))

        # Verifica si el usuario ya existe
        if Users.query.filter_by(nameUser=nameUser).first():
            flash('El usuario ya existe. Por favor elige otro.', 'danger')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(passwordUser)
        new_user = Users(nameUser=nameUser, passwordUser=hashed_password, rolUser=rolUser)

        db.session.add(new_user)
        db.session.commit()

        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template("register.html")
