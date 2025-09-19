# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/login'
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://brayan:brayanc@isladigital.xyz:3311/bd_brayan'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.abspath("instance/app.db")}'  # Ruta absoluta
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de email
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)