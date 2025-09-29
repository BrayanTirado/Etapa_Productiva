from app import create_app

app = create_app()

# Gunicorn necesita que la variable se llame "app"
# No corremos app.run() aquí, Gunicorn se encarga.
