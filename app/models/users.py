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
    tipo_documento = db.Column(db.Enum('Cedula de Ciudadania', 'Tarjeta de Identidad', 'Cedula Extrangeria', 'Registro Civil'), nullable=False)
    documento = db.Column(db.String(45), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    celular = db.Column(db.String(45), unique=True, nullable=False, index=True)
    ficha = db.Column(db.Enum('2931558','2674567','5434234'), nullable=False)
    password_aprendiz = db.Column(db.String(250), nullable=False)

    # 🔑 Clave foránea que conecta con contrato
    contrato_id = db.Column(db.Integer, db.ForeignKey('contrato.id_contrato'), nullable=True)

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
    tipo_contrato = db.Column(db.Enum('Contrato de Aprendizaje', 'Contrato laboral'), nullable=False)

    empresa_id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id_empresa'), nullable=False)

    # Relación inversa con aprendiz
    aprendices = db.relationship('Aprendiz', backref='contrato', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Contrato {self.tipo_contrato}>'


class Empresa(db.Model, UserMixin):
    __tablename__ = 'empresa'
    id_empresa = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(100), nullable=False)
    nit = db.Column(db.String(45), unique=True, nullable=False, index=True)
    direccion = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    correo_empresa = db.Column(db.String(100), nullable=False)

    contratos = db.relationship('Contrato', backref='empresa', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Empresa {self.nombre_empresa}>'


class Evidencia(db.Model):
    __tablename__ = 'evidencia'

    id_evidencia = db.Column(db.Integer, primary_key=True)
    formato = db.Column(db.String(10), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    url_archivo = db.Column(db.String(255), nullable=False)
    fecha_subida = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    nota = db.Column(db.String(255), nullable=True)  # Nuevo campo para mensaje/nota

    aprendiz_id_aprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.id_aprendiz'), nullable=False)

    def __repr__(self):
        return f'<Evidencia {self.nombre_archivo}>'


class Instructor(db.Model, UserMixin):
    __tablename__ = 'instructor'

    id_instructor = db.Column(db.Integer, primary_key=True)
    nombre_instructor = db.Column(db.String(45), nullable=False)
    apellido_instructor = db.Column(db.String(45), nullable=False)
    correo_instructor = db.Column(db.String(100), nullable=False)
    celular_instructor = db.Column(db.String(45), nullable=False)
    tipo_documento = db.Column(db.Enum('Cedula de Ciudadania','Cedula Extrangeria'), nullable=False)
    documento = db.Column(db.String(45), nullable=False)
    passwordInstructor = db.Column(db.String(250), nullable=False)

    programas = db.relationship('Programa', backref='instructor', lazy=True, cascade='all, delete-orphan')
    seguimientos = db.relationship('Seguimiento', backref='instructor', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Instructor {self.nombre_instructor} {self.apellido_instructor}>'

    def get_id(self):
         return f"instructor-{self.id_instructor}"

class Programa(db.Model):
    __tablename__ = 'programa'

    id_programa = db.Column(db.Integer, primary_key=True)
    nombre_programa = db.Column(db.String(45), nullable=False)
    titulo = db.Column(db.Enum('Auxiliar', 'Tecnico', 'Tecnologo'), nullable=False)
    jornada = db.Column(db.Enum('Mañana', 'Tarde', 'Noche'), nullable=False)
    centro_formacion = db.Column(db.Enum(
        'Centro de Electricidad, Electrónica y Telecomunicaciones - Bogotá',
        'Centro de Gestión Industrial - Bogotá',
        'Centro de Diseño y Metrología - Bogotá',
        'Centro Nacional Colombo Alemán - Barranquilla',
        'Centro de Comercio y Servicios - Bucaramanga',
        'Centro de Industria y la Construcción - Ibagué',
        'Centro Agropecuario La Granja - Espinal',
        'Centro de Automatización Industrial - Dosquebradas',
        'Centro de Servicios Financieros - Bogotá',
        'Centro de Gestión y Desarrollo Sostenible Surcolombiano - Neiva',
        'Centro de Formación en Actividad Física y Cultura - Bogotá',
        'Centro Internacional Náutico, Fluvial y Portuario - Cartagena',
        'Centro Minero - Sogamoso',
        'Centro Agroindustrial - Quindío',
        'Centro de Formación en Talento Humano en Salud - Bogotá',
        'Centro de Comercio y Turismo - Pereira',
        'Centro de Procesos Industriales y Construcción - Barrancabermeja'), nullable=False)

    aprendiz_id_aprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.id_aprendiz'), nullable=True)
    instructor_id_instructor = db.Column(db.Integer, db.ForeignKey('instructor.id_instructor'), nullable=True)

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
