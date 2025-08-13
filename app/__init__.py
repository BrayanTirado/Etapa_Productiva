# Importa Flask para crear la aplicación
from flask import Flask

# Importa SQLAlchemy para manejar la base de datos relacional
from flask_sqlalchemy import SQLAlchemy

# Importa LoginManager para gestionar sesiones de usuario
from flask_login import LoginManager

# Importa os para operaciones con variables de entorno (en este caso, generación de la clave secreta)
import os

# Crea una instancia global de SQLAlchemy. Esto permite que la base de datos se pueda inicializar con la aplicación luego.
db = SQLAlchemy()

# Crea una instancia global de LoginManager. Permite manejar autenticación y sesiones de usuario.
login_manager = LoginManager()

# Define la función factory que crea y configura la aplicación Flask
def create_app():
    # Crea la instancia principal de la aplicación Flask
    app = Flask(__name__)

    # Establece una clave secreta aleatoria. Sirve para proteger sesiones y cookies.
    app.config['SECRET_KEY'] = os.urandom(24)

    # Carga configuraciones adicionales desde un objeto Config definido en config.py
    app.config.from_object('config.Config')

    # Inicializa la extensión SQLAlchemy con la aplicación
    db.init_app(app)

    # Inicializa la extensión LoginManager con la aplicación
    login_manager.init_app(app)

    # Define la vista que se usará si un usuario no autenticado intenta acceder a contenido protegido
    login_manager.login_view = 'auth.login'

    # Función para cargar un usuario desde la base de datos por su id
    @login_manager.user_loader
    def load_user(idUser):
        # Importa aquí el modelo de usuario (import local para evitar importaciones circulares)
        from app.models.users import Users
        # Devuelve el objeto usuario correspondiente al id
        return Users.query.get(int(idUser))

    # Importa y registra todos los Blueprints (módulos de rutas) con alias cortos
    from app.routes.index_route import bp as index_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.empresa_route import bp as empresa_bp
    from app.routes.contrato_route import bp as contrato_bp
    from app.routes.aprendiz_route import bp as aprendiz_bp
    from app.routes.instructor_route import bp as instructor_bp
    from app.routes.programa_route import bp as programa_bp
    from app.routes.seguimiento_route import bp as seguimiento_bp
    from app.routes.evidencia_route import bp as evidencia_bp

    # Registra cada Blueprint en la aplicación
    app.register_blueprint(index_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(empresa_bp)
    app.register_blueprint(contrato_bp)
    app.register_blueprint(aprendiz_bp)
    app.register_blueprint(instructor_bp)
    app.register_blueprint(programa_bp)
    app.register_blueprint(seguimiento_bp)
    app.register_blueprint(evidencia_bp)

    # Devuelve la aplicación ya configurada
    return app
