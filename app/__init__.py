from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Se conecta a la base de datos
db = SQLAlchemy()

# Se crea una instancia global de LoginManager, usada para el control de inicio de sesión, autenticación y usuarios
login_manager = LoginManager()

def create_app():
    # 1. Crear la instancia principal de la aplicación
    app = Flask(__name__)

    # 2. Configuración de seguridad: establece una clave secreta desde variable de entorno o genera una aleatoria
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

    # 3. Carga configuraciones adicionalesdesde el archivo config.py (clase Config)
    app.config.from_object('config.Config')

    # Inicializa la base de datos con la app
    db.init_app(app)

    # Inicializa el administrador de login con la app
    login_manager.init_app(app)

    # Define la vista a la que se redirige cuando un usuario no autenticado intenta acceder a una ruta protegida
    login_manager.login_view = 'auth.login'

    # --- Importa los distintos módulos de rutas (organizados como Blueprints) ---
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

    # --- Registra cada Blueprint en la aplicación principal ---
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

    # Se asegura de que todas las tablas definidas en los modelos existan en la base de datos
    with app.app_context():
        db.create_all()

    # Devuelve la aplicación completamente configurada
    return app

# --- Función para cargar usuarios según su rol ---
@login_manager.user_loader
def load_user(user_id):
    from app.models.users import Aprendiz, Instructor, User

    try:
        role, id = user_id.split("-")
        id = int(id)
    except (ValueError, AttributeError):
        return None

    if role == "aprendiz":
        return Aprendiz.query.get(id)
    elif role == "instructor":
        return Instructor.query.get(id)
    elif role == "admin":
        return User.query.get(id)
    return None