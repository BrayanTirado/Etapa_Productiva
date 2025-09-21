from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import os
import sys

# --- Extensiones globales ---
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def check_email_config():
    """Verifica la configuración de email y muestra advertencias si es necesario"""
    print("=" * 50)
    print("VERIFICACIÓN DE CONFIGURACIÓN DE EMAIL")
    print("=" * 50)

    # Verificar variables de entorno
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_default_sender = os.environ.get('MAIL_DEFAULT_SENDER')

    print(f"MAIL_USERNAME: {'✓ Configurado' if mail_username else '✗ No configurado'}")
    print(f"MAIL_PASSWORD: {'✓ Configurado' if mail_password else '✗ No configurado'}")
    print(f"MAIL_DEFAULT_SENDER: {'✓ Configurado' if mail_default_sender else '✗ No configurado'}")

    if not all([mail_username, mail_password, mail_default_sender]):
        print("\n⚠️  ADVERTENCIA: Variables de entorno de email no configuradas")
        print("   El envío de emails no funcionará correctamente")
        print("   Asegúrate de configurar MAIL_USERNAME, MAIL_PASSWORD y MAIL_DEFAULT_SENDER")
    else:
        print(f"\n✓ Configuración básica OK - Usuario: {mail_username}")

    # Verificar configuración de Gmail
    if mail_username and mail_username.endswith('@gmail.com'):
        print("\n📧 Detectado Gmail - Recordatorios importantes:")
        print("   • Asegúrate de tener activada la autenticación de 2 factores")
        print("   • MAIL_PASSWORD debe ser una 'contraseña de aplicación', no tu contraseña normal")
        print("   • Crea una contraseña de aplicación en: https://myaccount.google.com/apppasswords")
        print("   • Verifica que no haya restricciones de seguridad en tu cuenta Gmail")

    print("=" * 50)
    print()

def create_app():
    """Crea y configura la aplicación Flask"""
    app = Flask(__name__)

    # Configuración de seguridad y base de datos
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config.from_object('config.Config')

    # Verificar configuración de email
    check_email_config()

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

