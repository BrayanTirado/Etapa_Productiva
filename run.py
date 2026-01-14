from app import create_app, db
from app.routes.sedes_route import insertar_sedes
import os

# -------------------------------
# Crear la aplicación (factory)
# -------------------------------
app = create_app()

# -------------------------------
# Inicialización automática de la BD
# Funciona en LOCAL y PRODUCCIÓN
# -------------------------------
def inicializar_base_de_datos():
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()

        # Insertar sedes SOLO si no existen
        try:
            insertar_sedes()
        except Exception as e:
            print("Inicialización de sedes omitida o ya existente:", e)

# Ejecutar inicialización SOLO una vez
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    inicializar_base_de_datos()

# -------------------------------
# Ejecución de la aplicación
# -------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))

    debug = os.environ.get(
        'FLASK_DEBUG', 'True'
    ).lower() in ('true', '1', 'yes')

    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
