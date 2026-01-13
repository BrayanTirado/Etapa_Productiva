from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
import os

# -------------------------
# Extensiones globales
# -------------------------
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

def create_app():
    """Crea y configura la aplicación Flask"""
    app = Flask(__name__)

    # -------------------------
    # Configuración básica
    # -------------------------
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config.from_object('config.Config')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # -------------------------
    # Configuración de Base de Datos
    # -------------------------
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Ajuste obligatorio para SQLAlchemy
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+psycopg2://", 1
            )
        elif not database_url.startswith("postgresql+psycopg2://"):
            database_url = "postgresql+psycopg2://" + database_url.split("://")[1]

        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"[DEBUG] Usando PostgreSQL desde env: {app.config['SQLALCHEMY_DATABASE_URI']}")
    else:
        # Fallback local (solo desarrollo)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{app.instance_path}/app.db"
        print(f"[DEBUG] Usando SQLite local: {app.config['SQLALCHEMY_DATABASE_URI']}")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -------------------------
    # Inicialización de extensiones
    # -------------------------
    db.init_app(app)
    migrate.init_app(app, db)   # 🔴 CLAVE PARA flask db
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

    os.makedirs(app.instance_path, exist_ok=True)

    # -------------------------
    # Importación de Blueprints
    # -------------------------
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
    from app.routes.crear_sede import bp as crear_sede_bp
    from app.routes.adm_route import adm_bp
    from app.routes.adm_sede_route import adm_sede_bp
    from app.routes.notificacion_route import notificacion_bp
    from app.routes.sedes_route import sedes_bp

    # -------------------------
    # Registro de Blueprints
    # -------------------------
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
    app.register_blueprint(crear_sede_bp)
    app.register_blueprint(adm_bp)
    app.register_blueprint(adm_sede_bp)
    app.register_blueprint(notificacion_bp)
    app.register_blueprint(sedes_bp)

    # -------------------------
    # Proxy reverso (Coolify / Nginx)
    # -------------------------
    proxy_fix_enabled = os.environ.get(
        'PROXY_FIX_ENABLED', 'true'
    ).lower() == 'true'

    if proxy_fix_enabled:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,
            x_proto=1,
            x_host=1,
            x_port=1,
            x_prefix=1
        )

    return app

# -------------------------
# Carga de usuario por rol
# -------------------------
@login_manager.user_loader
def load_user(user_id):
    from app.models.users import (
        Aprendiz, Instructor,
        Administrador, AdministradorSede
    )

    try:
        role, id = user_id.split("-")
        id = int(id)
    except (ValueError, AttributeError):
        return None

    if role == "aprendiz":
        return Aprendiz.query.get(id)
    elif role == "instructor":
        return Instructor.query.get(id)
    elif role == "administrador":
        return Administrador.query.get(id)
    elif role == "administrador_sede":
        return AdministradorSede.query.get(id)

    return None
