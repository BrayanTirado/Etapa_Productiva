from flask_login import UserMixin
from app import db

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id_user = db.Column(db.Integer, primary_key=True)
    name_user = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_user = db.Column(db.String(250), nullable=False)
    rol_user = db.Column(db.String(100), nullable=False)

    def get_id(self):
        return str(self.id_user)

class Aprendiz(db.Model, UserMixin):
    __tablename__ = 'aprendiz'

    id_aprendiz = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(45), nullable=False)
    apellido = db.Column(db.String(45), nullable=False)
    tipo_documento = db.Column(db.String(20), nullable=False)
    documento = db.Column(db.String(45), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    celular = db.Column(db.String(45), unique=True, nullable=False, index=True)
    ficha = db.Column(db.Integer, nullable=False)
    password_aprendiz = db.Column(db.String(250), nullable=False)
    contrato_id_contrato = db.Column(db.Integer, db.ForeignKey('contrato.id_contrato'), nullable=False)

    programas = db.relationship('Programa', backref='aprendiz', lazy=True, cascade='all, delete-orphan')
    seguimientos = db.relationship('Seguimiento', backref='aprendiz', lazy=True, cascade='all, delete-orphan')
    evidencias = db.relationship('Evidencia', backref='aprendiz', lazy=True, cascade='all, delete-orphan')

    def get_id(self):
        return f"aprendiz-{self.id_aprendiz}"

    def __repr__(self):
        return f'<Aprendiz {self.nombre} {self.apellido}>'

class Contrato(db.Model):
    __tablename__ = 'contrato'
    id_contrato = db.Column(db.Integer, primary_key=True)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    tipo_contrato = db.Column(db.String(100), nullable=False)
    empresa_id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id_empresa'), nullable=False)

    aprendices = db.relationship('Aprendiz', backref='contrato', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Contrato {self.tipo_contrato}>'

class Empresa(db.Model, UserMixin):
    __tablename__ = 'empresa'
    id_empresa = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(100), nullable=False)
    nit = db.Column(db.String(45), unique=True, nullable=False, index=True)
    sector = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    correo_empresa = db.Column(db.String(100), nullable=False)
    nombre_tutor = db.Column(db.String(100), nullable=False)
    cargo_tutor = db.Column(db.String(100), nullable=False)

    contratos = db.relationship('Contrato', backref='empresa', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Empresa {self.nombre_empresa}>'
    
class Evidencia(db.Model, UserMixin):
    __tablename__ = 'evidencia'

    id_evidencia = db.Column(db.Integer, primary_key=True)
    formato = db.Column(db.String(10), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    url_archivo = db.Column(db.String(255), nullable=False)
    fecha_subida = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)

    aprendiz_id_aprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.id_aprendiz'), nullable=False)

    def __repr__(self):
        return f'<Evidencia {self.nombre_archivo}>'

from flask_login import UserMixin
from app import db

class Instructor(db.Model, UserMixin):
    __tablename__ = 'instructor'

    id_instructor = db.Column(db.Integer, primary_key=True)
    nombre_instructor = db.Column(db.String(45), nullable=False)
    apellido_instructor = db.Column(db.String(45), nullable=False)
    correo_instructor = db.Column(db.String(100), nullable=False)
    celular_instructor = db.Column(db.String(45), nullable=False)
    tipo_documento = db.Column(db.String(5), nullable=False)
    documento = db.Column(db.String(45), nullable=False)
    passwordInstructor = db.Column(db.String(250), nullable=False)

    programas = db.relationship('Programa', backref='instructor', lazy=True, cascade='all, delete-orphan')
    seguimientos = db.relationship('Seguimiento', backref='instructor', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Instructor {self.nombre_instructor} {self.apellido_instructor}>'

    # ⚡ Importante: Flask-Login necesita este método si tu PK no se llama `id`
    def get_id(self):
         return f"instructor-{self.id_instructor}"

    
class Programa(db.Model, UserMixin):
    __tablename__ = 'programa'

    id_programa = db.Column(db.Integer, primary_key=True)
    nombre_programa = db.Column(db.String(45), nullable=False)
    nivel = db.Column(db.String(20), nullable=False)
    jornada = db.Column(db.String(20), nullable=False)
    centro_formacion = db.Column(db.String(45), nullable=False)

    aprendiz_id_aprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.id_aprendiz'), nullable=False)
    instructor_id_instructor = db.Column(db.Integer, db.ForeignKey('instructor.id_instructor'), nullable=False)

    def __repr__(self):
        return f'<Programa {self.nombre_programa}>'

class Seguimiento(db.Model):
    __tablename__ = 'seguimiento'

    id_seguimiento = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    observaciones = db.Column(db.String(255), nullable=False)

    instructor_id_instructor = db.Column(db.Integer, db.ForeignKey('instructor.id_instructor'), nullable=False)
    aprendiz_id_aprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.id_aprendiz'), nullable=False)

    def __repr__(self):
        return f'<Seguimiento {self.tipo} - {self.fecha}>'