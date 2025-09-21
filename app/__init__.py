from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import sys

# --- Extensiones globales ---
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()


def create_app():
    """Crea y configura la aplicación Flask"""
    app = Flask(__name__)

    # Configuración de seguridad y base de datos
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config.from_object('config.Config')

    # Inicializa extensiones
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

    # --- Importa modelos aquí para evitar import circular ---
    from app.models.users import Aprendiz, Instructor, Coordinador, Administrador, Sede, Empresa, Contrato, Programa, Seguimiento, Evidencia, Notificacion, PasswordResetToken

    # --- Importa Blueprints ---
    from app.routes.index_route import bp as index_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.empresa_route import bp as empresa_bp
    from app.routes.contrato_route import bp as contrato_bp
    from app.routes.instructor_route import bp as instructor_bp
    from app.routes.programa_route import bp as programa_bp
    from app.routes.seguimiento_route import bp as seguimiento_bp
    from app.routes.evidencia_route import bp as evidencia_bp
    from app.routes.listar_route import estudiantes_bp
    from app.routes.aprendiz_route import bp as aprendiz_bp
    from app.routes.coordinador_route import bp as coordinador_bp
    from app.routes.crear_sede import bp as crear_sede_bp
    from app.routes.crear_adm import bp as crear_adm_bp
    from app.routes.adm_route import adm_bp
    from app.routes.notificacion_route import notificacion_bp

    # --- Registra Blueprints ---
    app.register_blueprint(index_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(empresa_bp)
    app.register_blueprint(contrato_bp)
    app.register_blueprint(instructor_bp)
    app.register_blueprint(programa_bp)
    app.register_blueprint(seguimiento_bp)
    app.register_blueprint(evidencia_bp)
    app.register_blueprint(estudiantes_bp)
    app.register_blueprint(aprendiz_bp)
    app.register_blueprint(coordinador_bp)
    app.register_blueprint(crear_sede_bp)
    app.register_blueprint(crear_adm_bp)  # Aquí registramos el Blueprint corregido
    app.register_blueprint(adm_bp)
    app.register_blueprint(notificacion_bp)

    # --- Crea tablas en la base de datos ---
    with app.app_context():
        try:
            db.create_all()
            print("Conexión a la base de datos exitosa y tablas creadas.")
        except Exception as e:
            print(f"Error al conectar con la base de datos: {e}")
            raise

        # Email se maneja exclusivamente con Gmail API
        # No se requieren pruebas SMTP

    # --- Configuración para proxy reverso (PRODUCCIÓN) ---
    # Esto es necesario cuando Flask está detrás de un proxy reverso (Nginx, Apache, etc.)
    # Permite que Flask genere URLs externas correctamente en producción
    proxy_fix_enabled = os.environ.get('PROXY_FIX_ENABLED', 'true').lower() == 'true'

    if proxy_fix_enabled:
        print("[PROXY] Configurando ProxyFix para producción...")
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,      # Número de proxies para X-Forwarded-For
            x_proto=1,    # Número de proxies para X-Forwarded-Proto
            x_host=1,     # Número de proxies para X-Forwarded-Host
            x_port=1,     # Número de proxies para X-Forwarded-Port
            x_prefix=1    # Número de proxies para X-Forwarded-Prefix
        )
        print("[PROXY] ProxyFix configurado correctamente")
    else:
        print("[PROXY] ProxyFix deshabilitado (modo desarrollo)")

    return app

# --- Función para cargar usuarios según su rol ---
@login_manager.user_loader
def load_user(user_id):
    from app.models.users import Aprendiz, Instructor, Coordinador, Administrador

    try:
        role, id = user_id.split("-")
        id = int(id)
    except (ValueError, AttributeError):
        return None

    if role == "aprendiz":
        return Aprendiz.query.get(id)
    elif role == "instructor":
        return Instructor.query.get(id)
    elif role == "coordinador":
        return Coordinador.query.get(id)
    elif role == "administrador":
        return Administrador.query.get(id)
    return None

