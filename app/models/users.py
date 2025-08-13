from flask_login import UserMixin
from app import db

class Users(db.Model, UserMixin):
    __tablename__ = 'user'
    idUser = db.Column(db.Integer, primary_key=True)
    nameUser = db.Column(db.String(80), unique=True, nullable=False)
    passwordUser = db.Column(db.String(250), nullable=False)
    rolUser = db.Column(db.String(100), nullable=False)

   
    def get_id(self):
        return str(self.idUser)

class Aprendiz(db.Model):
    __tablename__ = 'aprendiz'

    idAprendiz = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(45), nullable=False)
    apellido = db.Column(db.String(45), nullable=False)
    tipo_documento = db.Column(db.String(20), nullable=False)
    documento = db.Column(db.String(45), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    celular = db.Column(db.String(45), unique=True, nullable=False)
    ficha = db.Column(db.Integer, nullable=False)
    Contrato_idContrato = db.Column(db.Integer, db.ForeignKey('contrato.idContrato'), nullable=False)

    programas = db.relationship('Programa', backref='aprendiz', lazy=True)
    seguimientos = db.relationship('Seguimiento', backref='aprendiz', lazy=True)
    evidencias = db.relationship('Evidencia', backref='aprendiz', lazy=True)

    def __repr__(self):
        return f'<Aprendiz {self.nombre} {self.apellido}>'

class Contrato(db.Model):
    __tablename__ = 'contrato'
    idContrato = db.Column(db.Integer, primary_key=True)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    tipo_contrato = db.Column(db.String(100), nullable=False)
    Empresa_idEmpresa = db.Column(db.Integer, db.ForeignKey('empresa.idEmpresa'), nullable=False)

    aprendices = db.relationship('Aprendiz', backref='contrato', lazy=True)
    def __repr__(self):
        return f'<Contrato {self.tipo_contrato}>'

class Empresa(db.Model):
    
    __tablename__ = 'empresa'
    idEmpresa = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(100), nullable=False)
    nit = db.Column(db.String(45), unique=True, nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    correo_empresa = db.Column(db.String(100), nullable=False)
    nombre_tutor = db.Column(db.String(100), nullable=False)
    cargo_tutor = db.Column(db.String(100), nullable=False)
    contratos = db.relationship('Contrato', backref='empresa', lazy=True)
    
    def __repr__(self):
        return f'<Empresa {self.nombre_empresa}>'
    
class Evidencia(db.Model):
    __tablename__ = 'evidencia'

    idEvidencia = db.Column(db.Integer, primary_key=True)
    formato = db.Column(db.String(10), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    url_archivo = db.Column(db.String(255), nullable=False)
    fecha_subida = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)

    Aprendiz_idAprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.idAprendiz'), nullable=False)

    def __repr__(self):
        return f'<Evidencia {self.nombre_archivo}>'

class Instructor(db.Model):
    __tablename__ = 'instructor'

    idInstructor = db.Column(db.Integer, primary_key=True)
    nombre_instructor = db.Column(db.String(45), nullable=False)
    apellido_instructor = db.Column(db.String(45), nullable=False)
    correo_instructor = db.Column(db.String(100), nullable=False)
    celular_instructor = db.Column(db.String(45), nullable=False)
    tipo_documento = db.Column(db.String(5), nullable=False)
    documento = db.Column(db.String(45), nullable=False)
    rol = db.Column(db.String(20), nullable=False)

    programas = db.relationship('Programa', backref='instructor', lazy=True)
    seguimientos = db.relationship('Seguimiento', backref='instructor', lazy=True)

    def __repr__(self):
        return f'<Instructor {self.nombre_instructor} {self.apellido_instructor}>'
    
class Programa(db.Model):
    __tablename__ = 'programa'

    idPrograma = db.Column(db.Integer, primary_key=True)
    nombre_programa = db.Column(db.String(45), nullable=False)
    nivel = db.Column(db.String(20), nullable=False)
    jornada = db.Column(db.String(20), nullable=False)
    centro_formacion = db.Column(db.String(45), nullable=False)

    Aprendiz_idAprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.idAprendiz'), nullable=False)
    Instructor_idInstructor = db.Column(db.Integer, db.ForeignKey('instructor.idInstructor'), nullable=False)

    def __repr__(self):
        return f'<Programa {self.nombre_programa}>'

class Seguimiento(db.Model):
    __tablename__ = 'seguimiento'

    idSeguimiento = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    observaciones = db.Column(db.String(255), nullable=False)

    Instructor_idInstructor = db.Column(db.Integer, db.ForeignKey('instructor.idInstructor'), nullable=False)
    Aprendiz_idAprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.idAprendiz'), nullable=False)

    def __repr__(self):
        return f'<Seguimiento {self.tipo} - {self.fecha}>'