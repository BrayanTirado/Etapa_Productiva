from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
from app.models.users import Evidencia, Aprendiz, Instructor
from app import db
import os
from werkzeug.utils import secure_filename
from datetime import date, datetime
from uuid import uuid4

bp = Blueprint('evidencia_bp', __name__, url_prefix='/evidencia')

# Carpeta donde se guardarán los archivos (misma lógica que tenías)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'Uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Extensiones permitidas por tipo (mayor control)
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

# --- LISTAR EVIDENCIAS SEGÚN ROL ---
@bp.route('/')
@login_required
def listar_evidencias():
    aprendiz_id = None

    # Aprendiz: solo sus evidencias
    if isinstance(current_user, Aprendiz):
        aprendiz_id = current_user.id_aprendiz

    # Instructor: puede pasar aprendiz_id por GET
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
    evidencias_excel = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Excel').all()
    evidencias_pdf = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Pdf').all()

    return render_template('evidencia/listar_evidencia.html',
                           aprendiz=aprendiz,
                           evidencias_word=evidencias_word,
                           evidencias_excel=evidencias_excel,
                           evidencias_pdf=evidencias_pdf,
                           now=datetime.now())

# --- SERVIR ARCHIVO PARA DESCARGA ---
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
        return redirect(url_for('evidencia_bp.listar_evidencias'))
    except Exception as e:
        flash(f'Error al servir el archivo: {str(e)}', 'danger')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

# --- VER PDF EN NAVEGADOR ---
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
        return redirect(url_for('evidencia_bp.listar_evidencias'))
    except Exception as e:
        flash(f'Error al abrir el archivo: {str(e)}', 'danger')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

# --- ELEGIR TIPO ---
@bp.route('/choose_type')
@login_required
def choose_type():
    if not isinstance(current_user, Aprendiz):
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))
    return render_template('evidencia/choose_type.html', now=datetime.now())

# --- SUBIR POR TIPO ---
@bp.route('/upload/<string:tipo>', methods=['GET', 'POST'])
@login_required
def upload_evidencia(tipo):
    """
    GET: muestra el formulario de subida (siempre permite mostrar el formulario).
    POST: intenta usar un registro vacío del tipo (si existe) o crea uno nuevo.
    """
    if not isinstance(current_user, Aprendiz):
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))

    if tipo not in EXTENSIONES_PERMITIDAS:
        flash('Tipo inválido.', 'danger')
        return redirect(url_for('evidencia_bp.choose_type'))

    # Si es GET, mostrar el formulario (antes bloqueaba si no había "hueco"; ahora mostramos)
    if request.method == 'GET':
        return render_template('evidencia/nueva_evidencia.html', tipo=tipo.capitalize(), now=datetime.now())

    # --- POST: procesar subida ---
    archivo = request.files.get('archivo')
    nota = request.form.get('nota', '').strip()

    if not archivo or not archivo.filename:
        flash('Debe seleccionar un archivo.', 'warning')
        return redirect(request.url)

    # Validar extensión según tipo
    if not allowed_file(archivo.filename, tipo):
        allowed_text = {
            'word': '(.doc, .docx)',
            'excel': '(.xls, .xlsx)',
            'pdf': '(.pdf)'
        }.get(tipo)
        flash(f'Archivo inválido. Solo se permiten {allowed_text}.', 'danger')
        return redirect(request.url)

    # Verificar límite de 17 evidencias subidas (solo las que ya tienen fecha/url)
    evidencias_subidas = Evidencia.query.filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz).filter(
        Evidencia.fecha_subida.isnot(None),
        Evidencia.url_archivo != ''
    ).count()
    if evidencias_subidas >= 17:
        flash('Has alcanzado el máximo de 17 evidencias subidas.', 'danger')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

    # Guardar archivo en carpeta (con uuid para evitar colisiones)
    original_name = secure_filename(archivo.filename)
    ext = original_name.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid4().hex}_{original_name}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_name)

    try:
        archivo.save(filepath)
    except Exception as e:
        flash(f'Error al guardar el archivo: {str(e)}', 'danger')
        return redirect(request.url)

    # Buscar una evidencia vacía del tipo especificado; si existe, la actualizamos.
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
        # Si no hay "hueco" pre-creado, creamos un nuevo registro para esta subida.
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

    db.session.commit()
    flash('Evidencia subida con éxito ✅', 'modal')
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
        flash('Evidencia actualizada correctamente ✅', 'success')
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
    flash('Evidencia eliminada correctamente ✅', 'success')
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
    evidencias_excel = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Excel').all()
    evidencias_pdf = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Pdf').all()

    return render_template('evidencia/listar_evidencia.html',
                           aprendiz=aprendiz,
                           evidencias_word=evidencias_word,
                           evidencias_excel=evidencias_excel,
                           evidencias_pdf=evidencias_pdf,
                           now=datetime.now())
