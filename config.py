# config.py
class Config:
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/login'
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://brayan:brayanc@isladigital.xyz:3311/bd_brayan'
    import os
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.abspath("instance/app.db")}'  # Ruta absoluta
    SQLALCHEMY_TRACK_MODIFICATIONS = False