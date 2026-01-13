from app import create_app, db
from app.routes.sedes_route import insertar_sedes
import os
from sqlalchemy import text

# -------------------------------
# Crear la aplicación usando la factory
# -------------------------------
app = create_app()

# -------------------------------
# Crear tablas automáticamente (solo para desarrollo)
# -------------------------------
# Nota: En producción es mejor usar migraciones con Flask-Migrate
with app.app_context():
    db.create_all()
    insertar_sedes()

    # Debug: Verificar columnas de la tabla aprendiz
    try:
        result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'aprendiz' ORDER BY column_name"))
        columns = [row[0] for row in result]
        print("Columnas en tabla 'aprendiz':", columns)
        if 'correo' not in columns:
            print("ERROR: La columna 'correo' no existe en la tabla 'aprendiz'")
        else:
            print("La columna 'correo' existe en la tabla 'aprendiz'")
    except Exception as e:
        print("Error al verificar columnas:", e)

# -------------------------------
# Configuración de ejecución
# -------------------------------
if __name__ == '__main__':
    # Puerto: por defecto 8080, pero puedes usar la variable de entorno PORT
    port = int(os.environ.get('PORT', 8080))

    # Debug: activado si FLASK_DEBUG es 'True', '1' o 'yes'
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes')

    # Activar recarga automática de templates
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Ejecutar servidor de desarrollo con auto-reload
    app.run(
        host='0.0.0.0',  # Permite acceder desde otras máquinas si estás en LAN
        port=port,
        debug=debug,     # debug=True activa auto-reload del código Python
        use_reloader=True  # Fuerza el recargador incluso si debug=False
    )

