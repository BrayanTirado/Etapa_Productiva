from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
from app.models.users import Evidencia, Aprendiz, Instructor
from app import db
import os
from werkzeug.utils import secure_filename
from datetime import date, datetime, timedelta
from uuid import uuid4

bp = Blueprint('evidencia_bp', __name__, url_prefix='/evidencia')

# -------------------------------
# VERIFICAR RESTRICCIÓN
# -------------------------------
def puede_subir_archivo(aprendiz_id, tipo, sesion_excel=None):
    from datetime import datetime, timedelta
    from models import Evidencia

    # Definir las restricciones en días
    restricciones = {
        'word': 90,
        'excel_15': 15,
        'excel_3': 90,
        'pdf': 0  # sin restricción
    }

    # Determinar clave según tipo + sesión
    if tipo == 'word':
        clave = 'word'
        etiqueta = "Word"
    elif tipo == 'excel' and sesion_excel == '15_dias':
        clave = 'excel_15'
        etiqueta = "Excel (sesión 15 días)"
    elif tipo == 'excel' and sesion_excel == '3_meses':
        clave = 'excel_3'
        etiqueta = "Excel (sesión 3 meses)"
    elif tipo == 'pdf':
        clave = 'pdf'
        etiqueta = "PDF"
    else:
        return True, None, None  # sin restricción por defecto

    dias_restriccion = restricciones.get(clave, 0)

    if dias_restriccion == 0:
        # PDF → nunca se restringe
        return True, None, None

    # Buscar última evidencia subida de ese tipo
    ultima = None
    if clave == 'word':
        ultima = Evidencia.query.filter_by(
            aprendiz_id=aprendiz_id,
            tipo='word'
        ).order_by(Evidencia.fecha_subida.desc()).first()
    elif clave == 'excel_15':
        ultima = Evidencia.query.filter_by(
            aprendiz_id=aprendiz_id,
            tipo='excel',
            sesion='15_dias'
        ).order_by(Evidencia.fecha_subida.desc()).first()
    elif clave == 'excel_3':
        ultima = Evidencia.query.filter_by(
            aprendiz_id=aprendiz_id,
            tipo='excel',
            sesion='3_meses'
        ).order_by(Evidencia.fecha_subida.desc()).first()

    if ultima:
        fecha_limite = ultima.fecha_subida + timedelta(days=dias_restriccion)
        if datetime.now() < fecha_limite:
            return False, (
                f"No puedes subir otro archivo {etiqueta}. "
                f"Debes esperar {dias_restriccion} días más."
            ), fecha_limite.strftime("%d/%m/%Y")

    return True, None, None

# -------------------------------
# MIGRACIÓN SESION_EXCEL
# -------------------------------
@bp.route('/migrar_sesion_excel')
@login_required
def migrar_sesion_excel():
    """Migra las evidencias existentes para asignar el campo sesion_excel correctamente."""
    if not isinstance(current_user, Aprendiz):
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))

    try:
        evidencias_sin_sesion = Evidencia.query.filter_by(
            tipo='Excel',
            sesion_excel=None
        ).all()

        actualizadas = 0
        for evidencia in evidencias_sin_sesion:
            if evidencia.primera_subida_excel_15:
                evidencia.sesion_excel = '15_dias'
                actualizadas += 1
            elif evidencia.primera_subida_excel_3:
                evidencia.sesion_excel = '3_meses'
                actualizadas += 1

        if actualizadas > 0:
            db.session.commit()
            flash(f'Migración completada. Se actualizaron {actualizadas} evidencias Excel.', 'success')
        else:
            flash('No se encontraron evidencias Excel para migrar.', 'info')

    except Exception as e:
        db.session.rollback()
        flash(f'Error en la migración: {str(e)}', 'danger')

    return redirect(url_for('evidencia_bp.listar_evidencias'))


# -------------------------------
# CONFIGURACIÓN ARCHIVOS
# -------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'Uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXTENSIONES_PERMITIDAS = {
    "word": {"doc", "docx"},
    "excel": {"xls", "xlsx"},
    "pdf": {"pdf"}
}


def allowed_file(filename: str, tipo: str) -> bool:
    """Valida que el archivo corresponda al tipo esperado (Word, Excel, PDF)."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in EXTENSIONES_PERMITIDAS.get(tipo, set())


def puede_subir_archivo(aprendiz_id: int, tipo: str, sesion_excel: str = None) -> tuple[bool, str, str]:
    """
    Verifica si un aprendiz puede subir un archivo según las restricciones temporales.
    Retorna (puede_subir, mensaje_error, fecha_proxima)
    """
    hoy = date.today()

    if tipo == 'word':
        primera_subida = db.session.query(Evidencia.primera_subida_word)\
            .filter_by(aprendiz_id_aprendiz=aprendiz_id)\
            .filter(Evidencia.primera_subida_word.isnot(None))\
            .order_by(Evidencia.primera_subida_word)\
            .first()

        if primera_subida and primera_subida[0]:
            dias_desde_primera = (hoy - primera_subida[0]).days
            if dias_desde_primera < 90:
                dias_restantes = 90 - dias_desde_primera
                fecha_proxima = primera_subida[0] + timedelta(days=90)
                return False, f"No puedes subir otro archivo Word. Debes esperar {dias_restantes} días más.", fecha_proxima.strftime('%d/%m/%Y')

    elif tipo == 'excel':
        if sesion_excel == '15_dias':
            primera_subida = db.session.query(Evidencia.primera_subida_excel_15)\
                .filter_by(aprendiz_id_aprendiz=aprendiz_id)\
                .filter(Evidencia.primera_subida_excel_15.isnot(None))\
                .order_by(Evidencia.primera_subida_excel_15)\
                .first()

            if not primera_subida or not primera_subida[0]:
                evidencia_mas_antigua = db.session.query(db.func.min(Evidencia.fecha_subida))\
                    .filter_by(aprendiz_id_aprendiz=aprendiz_id, tipo='Excel', sesion_excel='15_dias')\
                    .filter(Evidencia.fecha_subida.isnot(None))\
                    .first()
                if evidencia_mas_antigua and evidencia_mas_antigua[0]:
                    primera_subida = (evidencia_mas_antigua[0],)

            if primera_subida and primera_subida[0]:
                dias_desde_primera = (hoy - primera_subida[0]).days
                if dias_desde_primera < 15:   # ✔ ahora sí 15 días
                    dias_restantes = 15 - dias_desde_primera
            fecha_proxima = primera_subida[0] + timedelta(days=15)
            return False, f"No puedes subir otro archivo Excel (sesión 15 días). Debes esperar {dias_restantes} días más.", fecha_proxima.strftime('%d/%m/%Y')


        elif sesion_excel == '3_meses':
            primera_subida = db.session.query(Evidencia.primera_subida_excel_3)\
                .filter_by(aprendiz_id_aprendiz=aprendiz_id)\
                .filter(Evidencia.primera_subida_excel_3.isnot(None))\
                .order_by(Evidencia.primera_subida_excel_3)\
                .first()

            if not primera_subida or not primera_subida[0]:
                evidencia_mas_antigua = db.session.query(db.func.min(Evidencia.fecha_subida))\
                    .filter_by(aprendiz_id_aprendiz=aprendiz_id, tipo='Excel', sesion_excel='3_meses')\
                    .filter(Evidencia.fecha_subida.isnot(None))\
                    .first()
                if evidencia_mas_antigua and evidencia_mas_antigua[0]:
                    primera_subida = (evidencia_mas_antigua[0],)

            if primera_subida and primera_subida[0]:
                dias_desde_primera = (hoy - primera_subida[0]).days
                if dias_desde_primera < 90:
                    dias_restantes = 90 - dias_desde_primera
                    fecha_proxima = primera_subida[0] + timedelta(days=90)
                    return False, f"No puedes subir otro archivo Excel (sesión 3 meses). Debes esperar {dias_restantes} días más.", fecha_proxima.strftime('%d/%m/%Y')

    return True, "", ""


# -------------------------------
# LISTAR EVIDENCIAS
# -------------------------------
@bp.route('/')
@login_required
def listar_evidencias():
    aprendiz_id = None

    if isinstance(current_user, Aprendiz):
        aprendiz_id = current_user.id_aprendiz
    elif isinstance(current_user, Instructor):
        aprendiz_id = request.args.get('aprendiz_id', type=int)
        if not aprendiz_id:
            flash('Debes seleccionar un aprendiz.', 'warning')
            return redirect(url_for('auth.dashboard'))

    if not aprendiz_id:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))

    aprendiz = Aprendiz.query.get_or_404(aprendiz_id)

    evidencias_word = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Word').all()
    evidencias_excel_15 = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Excel', sesion_excel='15_dias').all()
    evidencias_excel_3 = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Excel', sesion_excel='3_meses').all()
    evidencias_pdf = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Pdf').all()

    return render_template('evidencia/listar_evidencia.html',
                           aprendiz=aprendiz,
                           evidencias_word=evidencias_word,
                           evidencias_excel_15=evidencias_excel_15,
                           evidencias_excel_3=evidencias_excel_3,
                           evidencias_pdf=evidencias_pdf,
                           now=datetime.now())


# -------------------------------
# DESCARGAR ARCHIVO
# -------------------------------
@bp.route('/archivo/<int:id>')
@login_required
def serve_file(id):
    evidencia = Evidencia.query.get_or_404(id)

    if isinstance(current_user, Aprendiz) and evidencia.aprendiz_id_aprendiz != current_user.id_aprendiz:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

    try:
        unique_filename = os.path.basename(evidencia.url_archivo)
        return send_from_directory(UPLOAD_FOLDER, unique_filename, as_attachment=True, download_name=evidencia.nombre_archivo)
    except FileNotFoundError:
        flash('El archivo no se encontró en el servidor.', 'danger')
    except Exception as e:
        flash(f'Error al servir el archivo: {str(e)}', 'danger')

    return redirect(url_for('evidencia_bp.listar_evidencias'))


# -------------------------------
# VER PDF EN NAVEGADOR
# -------------------------------
@bp.route('/ver/<int:id>')
@login_required
def view_file(id):
    evidencia = Evidencia.query.get_or_404(id)

    if isinstance(current_user, Aprendiz) and evidencia.aprendiz_id_aprendiz != current_user.id_aprendiz:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

    if evidencia.tipo.lower() != 'pdf':
        flash('Solo se pueden ver archivos PDF en el navegador.', 'warning')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

    try:
        unique_filename = os.path.basename(evidencia.url_archivo)
        return send_from_directory(UPLOAD_FOLDER, unique_filename, as_attachment=False)
    except FileNotFoundError:
        flash('El archivo no se encontró en el servidor.', 'danger')
    except Exception as e:
        flash(f'Error al abrir el archivo: {str(e)}', 'danger')

    return redirect(url_for('evidencia_bp.listar_evidencias'))


# -------------------------------
# ELEGIR TIPO
# -------------------------------
@bp.route('/choose_type')
@login_required
def choose_type():
    if not isinstance(current_user, Aprendiz):
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))
    return render_template('evidencia/choose_type.html', now=datetime.now())


# -------------------------------
# SUBIR EVIDENCIA
# -------------------------------
@bp.route('/upload/<string:tipo>', methods=['GET', 'POST'])
@login_required
def upload_evidencia(tipo):
    if not isinstance(current_user, Aprendiz):
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))

    if tipo not in EXTENSIONES_PERMITIDAS:
        flash('Tipo inválido.', 'danger')
        return redirect(url_for('evidencia_bp.choose_type'))

    # GET → mostrar formulario
    if request.method == 'GET':
        if tipo == 'excel':
            sesion_excel = request.args.get('sesion_excel', '15_dias')
            puede_subir, mensaje_error, fecha_proxima = puede_subir_archivo(current_user.id_aprendiz, tipo, sesion_excel)
        else:
            puede_subir, mensaje_error, fecha_proxima = puede_subir_archivo(current_user.id_aprendiz, tipo)

        if not puede_subir:
            return render_template('evidencia/choose_type.html',
                                   error_restriccion=True,
                                   mensaje_error=mensaje_error,
                                   fecha_proxima=fecha_proxima,
                                   now=datetime.now())

        return render_template('evidencia/nueva_evidencia.html', tipo=tipo.capitalize(), now=datetime.now())

    # POST → procesar subida
    archivo = request.files.get('archivo')
    nota = request.form.get('nota', '').strip()

    if not archivo or not archivo.filename:
        flash('Debe seleccionar un archivo.', 'warning')
        return redirect(request.url)

    if not allowed_file(archivo.filename, tipo):
        allowed_text = {
            'word': '(.doc, .docx)',
            'excel': '(.xls, .xlsx)',
            'pdf': '(.pdf)'
        }.get(tipo)
        flash(f'Archivo inválido. Solo se permiten {allowed_text}.', 'danger')
        return redirect(request.url)

    if tipo == 'excel':
        sesion_excel = request.form.get('sesion_excel', '15_dias')
        puede_subir, mensaje_error, fecha_proxima = puede_subir_archivo(current_user.id_aprendiz, tipo, sesion_excel)
    else:
        puede_subir, mensaje_error, fecha_proxima = puede_subir_archivo(current_user.id_aprendiz, tipo)

    if not puede_subir:
        return render_template('evidencia/choose_type.html',
                               error_restriccion=True,
                               mensaje_error=mensaje_error,
                               fecha_proxima=fecha_proxima,
                               now=datetime.now())

    evidencias_subidas = Evidencia.query.filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz).filter(
        Evidencia.fecha_subida.isnot(None),
        Evidencia.url_archivo != ''
    ).count()
    if evidencias_subidas >= 17:
        flash('Has alcanzado el máximo de 17 evidencias subidas.', 'danger')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

    original_name = secure_filename(archivo.filename)
    ext = original_name.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid4().hex}_{original_name}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_name)

    try:
        archivo.save(filepath)
    except Exception as e:
        flash(f'Error al guardar el archivo: {str(e)}', 'danger')
        return redirect(request.url)

    evidencia = Evidencia.query.filter_by(
        aprendiz_id_aprendiz=current_user.id_aprendiz,
        tipo=tipo.capitalize(),
        fecha_subida=None,
        url_archivo=''
    ).first()

    if evidencia:
        evidencia.formato = ext
        evidencia.nombre_archivo = original_name
        evidencia.url_archivo = filepath
        evidencia.fecha_subida = date.today()
        evidencia.nota = nota if nota else None
    else:
        evidencia = Evidencia(
            formato=ext,
            nombre_archivo=original_name,
            url_archivo=filepath,
            fecha_subida=date.today(),
            tipo=tipo.capitalize(),
            nota=nota if nota else None,
            aprendiz_id_aprendiz=current_user.id_aprendiz
        )
        db.session.add(evidencia)

    hoy = date.today()

    if tipo == 'word':
        existing_word = db.session.query(Evidencia.primera_subida_word)\
            .filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz)\
            .filter(Evidencia.primera_subida_word.isnot(None))\
            .first()
        evidencia.primera_subida_word = existing_word[0] if existing_word else hoy

    elif tipo == 'excel':
        sesion_excel = request.form.get('sesion_excel', '15_dias')
        evidencia.sesion_excel = sesion_excel

        if sesion_excel == '15_dias':
            existing_15 = db.session.query(Evidencia.primera_subida_excel_15)\
                .filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz)\
                .filter(Evidencia.primera_subida_excel_15.isnot(None))\
                .first()
            evidencia.primera_subida_excel_15 = existing_15[0] if existing_15 else hoy

        elif sesion_excel == '3_meses':
            existing_3 = db.session.query(Evidencia.primera_subida_excel_3)\
                .filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz)\
                .filter(Evidencia.primera_subida_excel_3.isnot(None))\
                .first()
            evidencia.primera_subida_excel_3 = existing_3[0] if existing_3 else hoy

    db.session.commit()

    from app.models.users import Notificacion
    try:
        instructor = current_user.instructor
        if instructor:
            tipo_archivo = tipo.capitalize()
            if tipo == 'excel':
                sesion_excel = request.form.get('sesion_excel', '15_dias')
                tipo_archivo = f"Excel ({'15 días' if sesion_excel == '15_dias' else '3 meses'})"

            motivo = "Nueva Evidencia subida"
            mensaje = f"El aprendiz {current_user.nombre} {current_user.apellido} ha Subido una nueva evidencia (ID: {evidencia.id_evidencia})."

            notificacion = Notificacion(
                motivo=motivo,
                mensaje=mensaje,
                remitente_id=current_user.id_aprendiz,
                rol_remitente="Aprendiz",
                destinatario_id=instructor.id_instructor,
                rol_destinatario="Instructor",
                visto=False
            )
            db.session.add(notificacion)
            db.session.commit()
    except Exception as e:
        db.session.rollback()

    flash('Evidencia subida con éxito [OK]', 'modal')
    return redirect(url_for('evidencia_bp.listar_evidencias'))

# --- EDITAR EVIDENCIA ---
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_evidencia(id):
    evidencia = Evidencia.query.get_or_404(id)

    print("Archivo en BD:", evidencia.nombre_archivo)

    if isinstance(current_user, Aprendiz) and evidencia.aprendiz_id_aprendiz != current_user.id_aprendiz:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

    if request.method == 'POST':
        nota = request.form.get('nota', '').strip()
        evidencia.nota = nota if nota else None
        evidencia.fecha_subida = date.today()

        archivo = request.files.get('archivo')
        if archivo and archivo.filename:
            tipo_actual = evidencia.tipo.lower()
            if not allowed_file(archivo.filename, tipo_actual):
                allowed_text = {
                    'word': '(.doc, .docx)',
                    'excel': '(.xls, .xlsx)',
                    'pdf': '(.pdf)'
                }.get(tipo_actual)
                flash(f'Archivo inválido. Solo se permiten {allowed_text}.', 'danger')
                return redirect(request.url)

            original_name = secure_filename(archivo.filename)
            ext = original_name.rsplit('.', 1)[1].lower()
            unique_name = f"{uuid4().hex}_{original_name}"
            new_filepath = os.path.join(UPLOAD_FOLDER, unique_name)

            try:
                archivo.save(new_filepath)
            except Exception as e:
                flash(f'Error al guardar el archivo nuevo: {str(e)}', 'danger')
                return redirect(request.url)

            # Eliminar archivo previo si existe
            try:
                if evidencia.url_archivo and os.path.exists(evidencia.url_archivo):
                    os.remove(evidencia.url_archivo)
            except Exception:
                pass

            evidencia.url_archivo = new_filepath
            evidencia.nombre_archivo = original_name
            evidencia.formato = ext

        db.session.commit()
        flash('Evidencia actualizada correctamente [OK]', 'success')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

    return render_template('evidencia/editar_evidencia.html', evidencia=evidencia, now=datetime.now())

# --- ELIMINAR EVIDENCIA ---
@bp.route('/eliminar/<int:id>')
@login_required
def eliminar_evidencia(id):
    evidencia = Evidencia.query.get_or_404(id)

    if isinstance(current_user, Aprendiz) and evidencia.aprendiz_id_aprendiz != current_user.id_aprendiz:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

    try:
        if evidencia.url_archivo and os.path.exists(evidencia.url_archivo):
            os.remove(evidencia.url_archivo)
    except Exception:
        pass

    db.session.delete(evidencia)
    db.session.commit()
    flash('Evidencia eliminada correctamente [OK]', 'success')
    return redirect(url_for('evidencia_bp.listar_evidencias'))

# --- LISTAR EVIDENCIAS DE UN APRENDIZ (INSTRUCTOR) ---
@bp.route('/aprendiz/<int:id_aprendiz>')
@login_required
def evidencias_aprendiz(id_aprendiz):
    if not isinstance(current_user, Instructor):
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))

    aprendiz = Aprendiz.query.get_or_404(id_aprendiz)

    evidencias_word = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Word').all()
    evidencias_excel_15 = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Excel', sesion_excel='15_dias').all()
    evidencias_excel_3 = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Excel', sesion_excel='3_meses').all()
    evidencias_pdf = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Pdf').all()

    return render_template('evidencia/listar_evidencia.html',
                            aprendiz=aprendiz,
                            evidencias_word=evidencias_word,
                            evidencias_excel_15=evidencias_excel_15,
                            evidencias_excel_3=evidencias_excel_3,
                            evidencias_pdf=evidencias_pdf,
                            now=datetime.now())
