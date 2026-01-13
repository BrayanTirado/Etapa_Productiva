from flask_login import UserMixin
from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import ENUM as PGEnum  # Opcional, pero útil si quieres explicitar

# -------------------------
# TABLA ADMINISTRADOR
# ------------------------->
class Administrador(db.Model, UserMixin):
    __tablename__ = "administrador"
    id_admin = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    tipo_documento = db.Column(
        db.Enum(
            'Cedula de Ciudadania',
            'Tarjeta de Identidad',
            'Cedula Extrangeria',
            'Registro Civil',
            name='tipo_documento_enum'  # ← Agregado name
        ),
        nullable=False
    )
    documento = db.Column(db.String(50), unique=True, nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    celular = db.Column(db.String(45), nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Relación con administradores de sede
    administradores_sede = db.relationship("AdministradorSede", back_populates="administrador_principal", lazy=True)

    @property
    def rol_user(self):
        return "administrador"

    def get_id(self):
        return f"administrador-{self.id_admin}"

# ------------------------->
# TABLA ADMINISTRADOR SEDE
# ------------------------->
class AdministradorSede(db.Model, UserMixin):
    __tablename__ = "administrador_sede"
    id_admin_sede = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    tipo_documento = db.Column(
        db.Enum(
            'Cedula de Ciudadania',
            'Tarjeta de Identidad',
            'Cedula Extrangeria',
            'Registro Civil',
            name='tipo_documento_enum'  # ← Agregado name
        ),
        nullable=False
    )
    documento = db.Column(db.String(50), unique=True, nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    celular = db.Column(db.String(45), nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Relación con administrador principal
    admin_principal_id = db.Column(db.Integer, db.ForeignKey('administrador.id_admin'), nullable=False)
    administrador_principal = db.relationship('Administrador', back_populates='administradores_sede')

    # Relación con sede asignada
    sede_id = db.Column(db.Integer, db.ForeignKey('sede.id_sede'), nullable=False)
    sede = db.relationship('Sede', backref='administrador_sede')

    # Relación con instructores que registra
    instructores = db.relationship('Instructor', back_populates='administrador_sede', lazy=True)

    @property
    def rol_user(self):
        return "administrador_sede"

    def get_id(self):
        return f"administrador_sede-{self.id_admin_sede}"

    def __repr__(self):
        return f'<AdministradorSede {self.nombre} {self.apellido} - Sede: {self.sede.nombre_sede if self.sede else "Sin sede"}>'

# -------------------------
# TABLA SEDE
# -------------------------
class Sede(db.Model):
    __tablename__ = 'sede'
    id_sede = db.Column(db.Integer, primary_key=True)
    nombre_sede = db.Column(db.String(50), nullable=False, unique=True)  # Usamos String en vez de Enum
    ciudad = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(100), nullable=True)
    token_expiracion = db.Column(db.DateTime, nullable=True)

    # Diccionario para mapear siglas a nombres largos
    nombres_completos = {
        'CGAO': 'CENTRO DE GESTIÓN AGROEMPRESARIAL DEL ORIENTE',
        'CCS': 'CENTRO DE CIENCIAS SOCIALES',
        'CDM': 'CENTRO DE DISEÑO Y MANUFACTURA',
        'CGAF': 'CENTRO DE GESTIÓN ADMINISTRATIVA Y FINANCIERA',
        'CGPI': 'CENTRO DE GESTIÓN PRODUCTIVA E INDUSTRIAL',
        'CTIC': 'CENTRO DE TECNOLOGÍAS DE INFORMACIÓN Y COMUNICACIÓN',
        'CBA': 'CENTRO DE BIOLOGÍA APLICADA',
        'CEM': 'CENTRO DE ENERGÍA Y MECÁNICA',
        'CSF': 'CENTRO DE SALUD Y FORMACIÓN',
        'CFGR': 'CENTRO DE FORMACIÓN GRÁFICA',
    }

    def nombre_completo(self):
        return f"{self.nombre_sede} - {self.nombres_completos.get(self.nombre_sede, '')}"

    def __repr__(self):
        return f'<Sede {self.nombre_completo()} - {self.ciudad}>'



# -------------------------
# TABLA INSTRUCTOR
# -------------------------
class Instructor(db.Model, UserMixin):
    __tablename__ = 'instructor'
    id_instructor = db.Column(db.Integer, primary_key=True)
    nombre_instructor = db.Column(db.String(45), nullable=False)
    apellido_instructor = db.Column(db.String(45), nullable=False)
    correo_instructor = db.Column(db.String(100), nullable=False, unique=True)
    celular_instructor = db.Column(db.String(45), nullable=False)
    tipo_documento = db.Column(
        db.Enum(
            'Cedula de Ciudadania',
            'Cedula Extrangeria',
            name='tipo_documento_instructor_enum'  # ← Agregado name (diferente para evitar conflicto)
        ),
        nullable=False
    )
    documento = db.Column(db.String(45), nullable=False, unique=True)
    password_instructor = db.Column(db.String(250), nullable=False)

    # Relación con administrador de sede que lo registra
    administrador_sede_id = db.Column(db.Integer, db.ForeignKey('administrador_sede.id_admin_sede'), nullable=False)
    administrador_sede = db.relationship('AdministradorSede', back_populates='instructores')

    sede_id = db.Column(db.Integer, db.ForeignKey('sede.id_sede'))
    sede = db.relationship('Sede', backref='instructores')

    programas = db.relationship('Programa', back_populates='instructor_rel', lazy=True, cascade='all, delete-orphan')
    seguimientos = db.relationship('Seguimiento', back_populates='instructor_rel', lazy=True, cascade='all, delete-orphan')
    aprendices_rel = db.relationship('Aprendiz', back_populates='instructor', lazy=True)

    @property
    def rol_user(self):
        return "instructor"

    def get_id(self):
        return f"instructor-{self.id_instructor}"

    def __repr__(self):
        return f'<Instructor {self.nombre_instructor} {self.apellido_instructor}>'

# -------------------------
# TABLA FICHA
# -------------------------
class Ficha(db.Model):
    __tablename__ = 'ficha'
    id_ficha = db.Column(db.Integer, primary_key=True)
    numero_ficha = db.Column(db.Integer, unique=True, nullable=False)

    programas_rel = db.relationship('Programa', back_populates='ficha_rel', lazy=True)
    sede_id = db.Column(db.Integer, db.ForeignKey('sede.id_sede'), nullable=False)
    sede_rel = db.relationship('Sede', backref='fichas', lazy=True)

# -------------------------
# TABLA PROGRAMA
# -------------------------
class Programa(db.Model):
    __tablename__ = 'programa'
    id_programa = db.Column(db.Integer, primary_key=True)
    nombre_programa = db.Column(db.String(45), nullable=False)
    titulo = db.Column(
        db.Enum('Auxiliar', 'Tecnico', 'Tecnologo', name='titulo_programa_enum'),  # ← Agregado
        nullable=False
    )
    # jornada removida, ahora en Aprendiz
    ficha_id = db.Column(db.Integer, db.ForeignKey('ficha.id_ficha'), nullable=False)
    instructor_id_instructor = db.Column(db.Integer, db.ForeignKey('instructor.id_instructor'), nullable=True)

    aprendices_rel = db.relationship('Aprendiz', back_populates='programa', lazy=True)
    instructor_rel = db.relationship('Instructor', back_populates='programas', lazy=True)
    ficha_rel = db.relationship('Ficha', back_populates='programas_rel', lazy=True)

    @property
    def ficha(self):
        return self.ficha_rel.numero_ficha if self.ficha_rel else None

# -------------------------
# TABLA APRENDIZ
# -------------------------
class Aprendiz(db.Model, UserMixin):
    __tablename__ = 'aprendiz'
    id_aprendiz = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(45), nullable=False)
    apellido = db.Column(db.String(45), nullable=False)
    tipo_documento = db.Column(
        db.Enum(
            'Cedula de Ciudadania',
            'Tarjeta de Identidad',
            'Cedula Extrangeria',
            'Registro Civil',
            name='tipo_documento_enum'  # ← Agregado (mismo que en otros, es válido)
        ),
        nullable=False
    )
    documento = db.Column(db.String(45), unique=True, nullable=False, index=True)
    correo = db.Column(db.String(100), unique=True, nullable=False, index=True)
    celular = db.Column(db.String(45), unique=True, nullable=False, index=True)
    jornada = db.Column(db.Enum('Mañana', 'Tarde', 'Noche', name='jornada_aprendiz_enum'), nullable=False)
    password_aprendiz = db.Column(db.String(250), nullable=False)

    contrato_id = db.Column(db.Integer, db.ForeignKey('contrato.id_contrato'), nullable=True)
    contrato = db.relationship('Contrato', back_populates='aprendices_rel', uselist=False)

    programa_id = db.Column(db.Integer, db.ForeignKey('programa.id_programa'), nullable=True)
    programa = db.relationship('Programa', back_populates='aprendices_rel')

    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id_instructor'), nullable=True)
    instructor = db.relationship('Instructor', back_populates='aprendices_rel')

    sede_id = db.Column(db.Integer, db.ForeignKey('sede.id_sede'), nullable=False)
    sede = db.relationship('Sede', backref='aprendices')

    empresas = db.relationship('Empresa', back_populates='aprendiz', cascade="all, delete-orphan")
    evidencias = db.relationship('Evidencia', back_populates='aprendiz_rel', lazy=True, cascade='all, delete-orphan')
    seguimiento = db.relationship('Seguimiento', back_populates='aprendiz_rel', lazy=True, uselist=False, cascade='all, delete-orphan')
    
    @property
    def rol_user(self):
        return "aprendiz"

    def get_id(self):
        return f"aprendiz-{self.id_aprendiz}"

    def __repr__(self):
        return f'<Aprendiz {self.nombre} {self.apellido}>'

# -------------------------
# TABLA CONTRATO
# -------------------------
class Contrato(db.Model):
    __tablename__ = 'contrato'
    id_contrato = db.Column(db.Integer, primary_key=True)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    tipo_contrato = db.Column(
        db.Enum('Contrato de Aprendizaje', 'Contrato laboral', name='tipo_contrato_enum'),  # ← Agregado
        nullable=False
    )

    empresa_id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id_empresa'), nullable=False)
    empresa = db.relationship('Empresa', back_populates='contratos')

    aprendices_rel = db.relationship('Aprendiz', back_populates='contrato', lazy=True)

    def __repr__(self):
        return f'<Contrato {self.tipo_contrato}>'

# -------------------------
# TABLA EMPRESA
# -------------------------
class Empresa(db.Model, UserMixin):
    __tablename__ = 'empresa'
    id_empresa = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(100), nullable=False)
    nit = db.Column(db.String(45), unique=True, nullable=False, index=True)
    direccion = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    correo_empresa = db.Column(db.String(100), nullable=False)
    nombre_jefe = db.Column(db.String(150), nullable=False, unique=True)
    correo_jefe = db.Column(db.String(150), nullable=False, unique=True)
    telefono_jefe = db.Column(db.String(50), nullable=False, unique=True)

    aprendiz_id_aprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.id_aprendiz'), nullable=False)
    aprendiz = db.relationship('Aprendiz', back_populates='empresas')

    contratos = db.relationship('Contrato', back_populates='empresa', lazy=True, cascade='all, delete-orphan')

# -------------------------
# TABLA EVIDENCIA
# -------------------------
class Evidencia(db.Model):
    __tablename__ = 'evidencia'
    id_evidencia = db.Column(db.Integer, primary_key=True)
    formato = db.Column(db.String(10), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    url_archivo = db.Column(db.String(255), nullable=False)
    fecha_subida = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    nota = db.Column(db.String(255), nullable=True)

    primera_subida_word = db.Column(db.Date, nullable=True)  
    primera_subida_excel_15 = db.Column(db.Date, nullable=True)  
    primera_subida_excel_3 = db.Column(db.Date, nullable=True)  
    primera_subida_pdf = db.Column(db.Date, nullable=True)

    sesion_excel = db.Column(db.String(20), nullable=True)  

    aprendiz_id_aprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.id_aprendiz'), nullable=False)
    aprendiz_rel = db.relationship('Aprendiz', back_populates='evidencias', lazy=True)

# -------------------------
# TABLA SEGUIMIENTO
# -------------------------
class Seguimiento(db.Model):
    __tablename__ = 'seguimiento'
    id_seguimiento = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    observaciones = db.Column(db.String(255), nullable=False)

    instructor_id_instructor = db.Column(db.Integer, db.ForeignKey('instructor.id_instructor'), nullable=False)
    aprendiz_id_aprendiz = db.Column(db.Integer, db.ForeignKey('aprendiz.id_aprendiz'), nullable=False, unique=True)

    instructor_rel = db.relationship('Instructor', back_populates='seguimientos', lazy=True)
    aprendiz_rel = db.relationship('Aprendiz', back_populates='seguimiento', lazy=True)

    def __repr__(self):
        return f'<Seguimiento {self.tipo} - {self.fecha}>'


# -------------------------
# TABLA TOKEN INSTRUCTOR
# -------------------------
class TokenInstructor(db.Model):
    __tablename__ = 'token_instructor'
    id_token = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), nullable=False, unique=True)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    sede_id = db.Column(db.Integer, db.ForeignKey('sede.id_sede'), nullable=False)
    sede = db.relationship('Sede', backref='tokens_instructor')

    def __repr__(self):
        return f"<TokenInstructor {self.token} - Válido hasta {self.fecha_expiracion} - Sede {self.sede_id}>"

# -------------------------
# TABLA PASSWORD RESET TOKEN
# -------------------------
class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_token'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    user_type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used = db.Column(db.Boolean, default=False, index=True)

    def is_expired(self):
        try:
            current_time = datetime.utcnow()
            expires_time = self.expires_at
            if expires_time.tzinfo is not None:
                expires_time = expires_time.replace(tzinfo=None)
            return current_time > expires_time
        except Exception:
            return True  # Por seguridad, si hay error → expirado

# -------------------------
# TABLA NOTIFICACION
# -------------------------
class Notificacion(db.Model):
    __tablename__ = 'notificacion'
    id = db.Column(db.Integer, primary_key=True)
    motivo = db.Column(db.String(100), nullable=True)
    mensaje = db.Column(db.Text, nullable=False)
    remitente_id = db.Column(db.Integer, nullable=False)
    rol_remitente = db.Column(db.String(50), nullable=False)
    destinatario_id = db.Column(db.Integer, nullable=True)
    rol_destinatario = db.Column(db.String(50), nullable=True)
    visto = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)