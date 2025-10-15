from flask_login import UserMixin
from datetime import datetime
from app import db

# -------------------------
# TABLA ADMINISTRADOR
# -------------------------
class Administrador(db.Model, UserMixin):
    __tablename__ = "administrador"
    id_admin = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    tipo_documento = db.Column(db.Enum(
        'Cedula de Ciudadania',
        'Tarjeta de Identidad',
        'Cedula Extrangeria',
        'Registro Civil'
    ), nullable=False)
    documento = db.Column(db.String(50), unique=True, nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    celular = db.Column(db.String(45), nullable=False)
    password = db.Column(db.String(200), nullable=False)

    tokens_coordinador = db.relationship("TokenCoordinador", back_populates="administrador", lazy=True)
    
    @property
    def rol_user(self):
        return "administrador"
    
    def get_id(self):
        return f"administrador-{self.id_admin}"

# -------------------------
# TABLA SEDE
# -------------------------
class Sede(db.Model):
    __tablename__ = 'sede'
    id_sede = db.Column(db.Integer, primary_key=True)
    nombre_sede = db.Column(db.Enum(
        'CGAO - CENTRO DE GESTIÓN AGROEMPRESARIAL DEL ORIENTE',
        'CCS - CENTRO DE COMERCIO Y SERVICIOS',
        'CDM - CENTRO DE DISEÑO Y METROLOGÍA',
        'CGAF - CENTRO DE GESTIÓN ADMINISTRATIVA Y FINANCIERA',
        'CGPI - CENTRO DE GESTIÓN DE LA PRODUCCIÓN INDUSTRIAL',
        'CTIC - CENTRO DE TECNOLOGÍA DE LA INFORMACIÓN Y COMUNICACIONES',
        'CBA - CENTRO DE BIOTECNOLOGÍA AGROPECUARIA',
        'CEM - CENTRO DE ENERGÍA Y MINAS',
        'CSF - CENTRO DE SERVICIOS FINANCIEROS',
        'CFGR - CENTRO DE FORMACIÓN EN GESTIÓN DEL RIESGO'
    ), nullable=False, unique=True)
    ciudad = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(100), nullable=True)  
    token_expiracion = db.Column(db.DateTime, nullable=True)

    coordinadores = db.relationship('Coordinador', back_populates='sede', lazy=True)
    def __repr__(self):
        return f'<Sede {self.nombre_sede} - {self.ciudad}>'

# -------------------------
# TABLA COORDINADOR
# -------------------------
class Coordinador(db.Model, UserMixin):
    __tablename__ = 'coordinador'
    id_coordinador = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(45), nullable=False)
    apellido = db.Column(db.String(45), nullable=False)
    tipo_documento = db.Column(db.Enum(
        'Cedula de Ciudadania',
        'Tarjeta de Identidad',
        'Cedula Extrangeria',
        'Registro Civil'
    ), nullable=False)
    documento = db.Column(db.String(45), unique=True, nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    celular = db.Column(db.String(45), nullable=False)
    password = db.Column(db.String(250), nullable=False)

    sede_id = db.Column(db.Integer, db.ForeignKey('sede.id_sede'), nullable=True)
    sede = db.relationship('Sede', back_populates='coordinadores')

    instructores = db.relationship('Instructor', back_populates='coordinador', lazy=True)
    tokens = db.relationship('TokenInstructor', back_populates='coordinador', lazy=True)

    @property
    def rol_user(self):
        return "coordinador"

    def get_id(self):
        return f"coordinador-{self.id_coordinador}"

    def __repr__(self):
        return f'<Coordinador {self.nombre} {self.apellido}>'

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
    tipo_documento = db.Column(db.Enum('Cedula de Ciudadania','Cedula Extrangeria'), nullable=False)
    documento = db.Column(db.String(45), nullable=False, unique=True)
    password_instructor = db.Column(db.String(250), nullable=False)

    coordinador_id = db.Column(db.Integer, db.ForeignKey('coordinador.id_coordinador'), nullable=False)
    coordinador = db.relationship('Coordinador', back_populates='instructores')

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

# -------------------------
# TABLA PROGRAMA
# -------------------------
class Programa(db.Model):
    __tablename__ = 'programa'
    id_programa = db.Column(db.Integer, primary_key=True)
    nombre_programa = db.Column(db.String(45), nullable=False)
    titulo = db.Column(db.Enum('Auxiliar', 'Tecnico', 'Tecnologo'), nullable=False)
    jornada = db.Column(db.Enum('Mañana', 'Tarde', 'Noche'), nullable=False)
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
    tipo_documento = db.Column(db.Enum(
        'Cedula de Ciudadania',
        'Tarjeta de Identidad',
        'Cedula Extrangeria',
        'Registro Civil'
    ), nullable=False)
    documento = db.Column(db.String(45), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    celular = db.Column(db.String(45), unique=True, nullable=False, index=True)
    password_aprendiz = db.Column(db.String(250), nullable=False)

    contrato_id = db.Column(db.Integer, db.ForeignKey('contrato.id_contrato'), nullable=True)
    contrato = db.relationship('Contrato', back_populates='aprendices_rel', uselist=False)

    programa_id = db.Column(db.Integer, db.ForeignKey('programa.id_programa'), nullable=True)
    programa = db.relationship('Programa', back_populates='aprendices_rel')

    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id_instructor'), nullable=True)
    instructor = db.relationship('Instructor', back_populates='aprendices_rel')

    sede_id = db.Column(db.Integer, db.ForeignKey('sede.id_sede'))
    sede = db.relationship('Sede', backref='aprendices')

    empresas = db.relationship('Empresa', back_populates='aprendiz', cascade="all, delete-orphan")
    evidencias = db.relationship('Evidencia', back_populates='aprendiz_rel', lazy=True, cascade='all, delete-orphan')
    seguimiento = db.relationship('Seguimiento', back_populates='aprendiz_rel', lazy=True, uselist=False, cascade='all, delete-orphan')

    coordinador_id = db.Column(db.Integer, db.ForeignKey('coordinador.id_coordinador'), nullable=True)
    coordinador = db.relationship('Coordinador', backref='aprendices', lazy=True)
    
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
    tipo_contrato = db.Column(db.Enum('Contrato de Aprendizaje', 'Contrato laboral'), nullable=False)

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

    # Nuevos campos para control de tiempo
    primera_subida_word = db.Column(db.Date, nullable=True)  
    primera_subida_excel_15 = db.Column(db.Date, nullable=True)  
    primera_subida_excel_3 = db.Column(db.Date, nullable=True)  
    primera_subida_pdf = db.Column(db.Date, nullable=True)

    # Campo para indicar la sesión específica de Excel
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
# TABLA TOKEN COORDINADOR
# -------------------------
class TokenCoordinador(db.Model):
    __tablename__ = "token_coordinador"
    id_token = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(50), unique=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_expiracion = db.Column(db.DateTime, nullable=True)
    usado = db.Column(db.Boolean, default=False)
    usado_para_sede = db.Column(db.Boolean, default=False)

    admin_id = db.Column(db.Integer, db.ForeignKey("administrador.id_admin"), nullable=False)
    administrador = db.relationship("Administrador", back_populates="tokens_coordinador")

    def __repr__(self):
        return f"<TokenCoordinador {self.token} - Usado: {self.usado} - Usado para sede: {self.usado_para_sede}>"

# -------------------------
# TABLA TOKEN INSTRUCTOR
# -------------------------
class TokenInstructor(db.Model):
    __tablename__ = 'token_instructor'

    id_token = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), nullable=False, unique=True)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    coordinador_id = db.Column(db.Integer, db.ForeignKey('coordinador.id_coordinador'), nullable=False)
    coordinador = db.relationship('Coordinador', back_populates='tokens')

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
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)  # Agregado índice
    email = db.Column(db.String(100), nullable=False, index=True)  # Agregado índice
    user_type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, nullable=False, index=True)  # Agregado índice
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # Agregado índice
    expires_at = db.Column(db.DateTime, nullable=False, index=True)  # Agregado índice
    used = db.Column(db.Boolean, default=False, index=True)  # Agregado índice

    def is_expired(self):
        """Verificar si el token ha expirado con manejo optimizado de zona horaria"""
        try:
            # Obtener tiempo actual en UTC
            current_time = datetime.utcnow()
            print(f"[DEBUG] Verificando expiración del token:")
            print(f"[DEBUG]   Current time (UTC): {current_time}")
            print(f"[DEBUG]   Token expires_at: {self.expires_at}")
            print(f"[DEBUG]   Token expires_at type: {type(self.expires_at)}")

            # Asegurar que expires_at no tenga zona horaria para comparación consistente
            expires_time = self.expires_at
            if hasattr(expires_time, 'replace') and hasattr(expires_time, 'tzinfo') and expires_time.tzinfo is not None:
                expires_time = expires_time.replace(tzinfo=None)
                print(f"[DEBUG]   Converted expires_time (no timezone): {expires_time}")
            else:
                # Si no tiene zona horaria, asumir que ya está en UTC
                print(f"[DEBUG]   expires_time already without timezone: {expires_time}")

            # Comparación directa
            is_expired = current_time.replace(tzinfo=None) > expires_time
            print(f"[DEBUG]   Is expired: {is_expired}")
            print(f"[DEBUG]   Time difference: {(current_time.replace(tzinfo=None) - expires_time).total_seconds()} seconds")

            return is_expired

        except Exception as e:
            # En caso de error, considerar el token como expirado por seguridad
            print(f"[ERROR] Error verificando expiración del token: {e}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return True

# -------------------------
# TABLA NOTIFICACION
# -------------------------
class Notificacion(db.Model):
    __tablename__ = 'notificacion'
    id = db.Column(db.Integer, primary_key=True)
    motivo = db.Column(db.String(100), nullable=True)  # Nuevo campo para el motivo/asunto de la notificación
    mensaje = db.Column(db.Text, nullable=False)
    remitente_id = db.Column(db.Integer, nullable=False)
    rol_remitente = db.Column(db.String(50), nullable=False)
    destinatario_id = db.Column(db.Integer, nullable=True)
    rol_destinatario = db.Column(db.String(50), nullable=True)
    visto = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
