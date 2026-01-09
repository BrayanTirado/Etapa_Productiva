# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    # ============================
    # ARCHIVOS SUBIDOS (SIEMPRE)
    # ============================

    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(__file__),
        'app',
        'static',
        'uploads'
    )

    # ============================
    # BASE DE DATOS
    # ============================

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://",
                "postgresql+psycopg2://",
                1
            )
        elif not database_url.startswith("postgresql+psycopg2://"):
            database_url = "postgresql+psycopg2://" + database_url.split("://")[1]

        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///instance/app.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ============================
    # POOL
    # ============================

    SQLALCHEMY_POOL_SIZE = 5
    SQLALCHEMY_POOL_TIMEOUT = 20
    SQLALCHEMY_POOL_RECYCLE = 1800
    SQLALCHEMY_MAX_OVERFLOW = 10

    # ============================
    # EMAIL
    # ============================

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv(
        'MAIL_DEFAULT_SENDER',
        MAIL_USERNAME
    )

    # ============================
    # PRODUCCIÓN
    # ============================

    SERVER_NAME = os.getenv('SERVER_NAME')
    PREFERRED_URL_SCHEME = os.getenv(
        'PREFERRED_URL_SCHEME',
        'https'
    )
