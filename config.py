# config.py

class Config:
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/login'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///flaskdb.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False