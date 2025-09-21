# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base de datos principal (MySQL remoto)
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://brayan:brayanc@isladigital.xyz:3311/bd_brayan'

    # Fallback a SQLite local si hay problemas de conectividad
    # Descomenta la siguiente línea si la BD remota está lenta:
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/app.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de pool de conexiones para mejor rendimiento
    SQLALCHEMY_POOL_SIZE = 5  # Reducido para conexiones remotas
    SQLALCHEMY_POOL_TIMEOUT = 20  # Timeout reducido a 20 segundos
    SQLALCHEMY_POOL_RECYCLE = 1800  # Reciclar conexiones cada 30 minutos
    SQLALCHEMY_MAX_OVERFLOW = 10

    # Configuración de email
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    # Configuración para URLs externas (necesario para producción)
    SERVER_NAME = os.environ.get('SERVER_NAME')  # Ej: 'tu-dominio.com'
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'https')  # 'https' para producción