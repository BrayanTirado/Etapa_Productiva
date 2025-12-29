from app import create_app, db
import os

# Crea la aplicación usando la factory
app = create_app()

# Crea las tablas si no existen (solo útil en desarrollo o primera ejecución)
# En producción, es mejor usar migraciones (Flask-Migrate)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Ejecución LOCAL (cuando corres python run.py o python app.py)
    # - Usa el servidor de desarrollo de Flask
    # - Debug solo si está activado explícitamente (por seguridad)
    # - Puerto por defecto 8080, pero permite override con variable PORT
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )