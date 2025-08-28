from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
from app.models.users import Evidencia, Aprendiz
from app import db
import os
from werkzeug.utils import secure_filename
from datetime import date
from uuid import uuid4

bp = Blueprint('evidencia_bp', __name__, url_prefix='/evidencia')

# Carpeta donde se guardarán los archivos (ajustada con base_dir)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Soportar tanto formatos antiguos como nuevos
ALLOWED_EXTENSIONS = {'doc', 'docx', 'xls', 'xlsx'}


def allowed_file(filename: str, tipo: str) -> bool:
    """
    Verifica la extensión según el tipo ('word' o 'excel').
    """
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if tipo == 'word':
        return ext in {'doc', 'docx'}
    elif tipo == 'excel':
        return ext in {'xls', 'xlsx'}
    return False


# --- SERVIR ARCHIVO ---
@bp.route('/archivo/<int:id>')
@login_required
def serve_file(id):
    evidencia = Evidencia.query.get_or_404(id)

    if evidencia.aprendiz_id_aprendiz != current_user.id_aprendiz:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('evidencia_bp.mis_evidencias'))

    try:
        # El archivo se guarda con nombre único en UPLOAD_FOLDER
        unique_filename = os.path.basename(evidencia.url_archivo)

        return send_from_directory(
            UPLOAD_FOLDER,                 # 👈 siempre desde la carpeta configurada
            unique_filename,               # 👈 nombre físico único
            as_attachment=True,
            download_name=evidencia.nombre_archivo  # 👈 nombre original para el usuario
        )
    except FileNotFoundError:
        flash('El archivo no se encontró en el servidor.', 'danger')
        return redirect(url_for('evidencia_bp.mis_evidencias'))
    except Exception as e:
        flash(f'Error al servir el archivo: {str(e)}', 'danger')
        return redirect(url_for('evidencia_bp.mis_evidencias'))




# --- ELEGIR TIPO ---
@bp.route('/choose_type')
@login_required
def choose_type():
    if not isinstance(current_user, Aprendiz):
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))
    return render_template('evidencia/choose_type.html')


# --- SUBIR POR TIPO ---
@bp.route('/upload/<string:tipo>', methods=['GET', 'POST'])
@login_required
def upload_evidencia(tipo):
    if not isinstance(current_user, Aprendiz):
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))

    if tipo not in ['word', 'excel']:
        flash('Tipo inválido.', 'danger')
        return redirect(url_for('evidencia_bp.choose_type'))

    if request.method == 'POST':
        archivo = request.files.get('archivo')
        nota = request.form.get('nota', '').strip()

        if not archivo or not archivo.filename:
            flash('Debe seleccionar un archivo.', 'warning')
            return redirect(request.url)

        if not allowed_file(archivo.filename, tipo):
            allowed_text = '(.doc, .docx)' if tipo == 'word' else '(.xls, .xlsx)'
            flash(f'Archivo inválido. Solo se permiten {allowed_text}.', 'danger')
            return redirect(request.url)

        original_name = secure_filename(archivo.filename)   # 👈 lo que verá el usuario
        ext = original_name.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid4().hex}_{original_name}"      # 👈 lo que se guarda en disco
        filepath = os.path.join(UPLOAD_FOLDER, unique_name)
        try:
            archivo.save(filepath)
        except Exception as e:
            flash(f'Error al guardar el archivo: {str(e)}', 'danger')
            return redirect(request.url)

        nueva = Evidencia(
            formato=ext,
            nombre_archivo=original_name,   # 👈 guardamos limpio
            url_archivo=filepath,           # 👈 guardamos ruta real
            fecha_subida=date.today(),
            tipo='Word' if tipo == 'word' else 'Excel',
            nota=nota if nota else None,
            aprendiz_id_aprendiz=current_user.id_aprendiz
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Evidencia subida con éxito ✅', 'success')
        return redirect(url_for('evidencia_bp.mis_evidencias'))

    return render_template('evidencia/nueva_evidencia.html', tipo=tipo.capitalize())


# --- LISTAR MIS EVIDENCIAS ---
@bp.route('/mis_evidencias')
@login_required
def mis_evidencias():
    if not isinstance(current_user, Aprendiz):
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))
    evidencias_word = Evidencia.query.filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz, tipo='Word').all()
    evidencias_excel = Evidencia.query.filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz, tipo='Excel').all()
    return render_template('evidencia/listar_evidencia.html',
                           evidencias_word=evidencias_word, evidencias_excel=evidencias_excel)


# --- LISTAR TODAS ---
@bp.route('/')
@login_required
def listar_evidencias():
    evidencias_word = Evidencia.query.filter_by(tipo='Word').all()
    evidencias_excel = Evidencia.query.filter_by(tipo='Excel').all()
    return render_template('evidencia/listar_evidencia.html',
                           evidencias_word=evidencias_word, evidencias_excel=evidencias_excel)


# --- EDITAR ---
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_evidencia(id):
    evidencia = Evidencia.query.get_or_404(id)
    if evidencia.aprendiz_id_aprendiz != current_user.id_aprendiz:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('evidencia_bp.mis_evidencias'))

    if request.method == 'POST':
        nota = request.form.get('nota', '').strip()
        evidencia.nota = nota if nota else None
        evidencia.fecha_subida = date.today()

        archivo = request.files.get('archivo')
        if archivo and archivo.filename:
            tipo_actual = evidencia.tipo.lower()
            if not allowed_file(archivo.filename, tipo_actual):
                allowed_text = '(.doc, .docx)' if tipo_actual == 'word' else '(.xls, .xlsx)'
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

            # Borrar el archivo anterior
            try:
                if evidencia.url_archivo and os.path.exists(evidencia.url_archivo):
                    os.remove(evidencia.url_archivo)
            except Exception:
                pass

            evidencia.url_archivo = new_filepath
            evidencia.nombre_archivo = original_name   # 👈 limpio para mostrar
            evidencia.formato = ext

        db.session.commit()
        flash('Evidencia actualizada correctamente ✅', 'success')
        return redirect(url_for('evidencia_bp.mis_evidencias'))

    return render_template('evidencia/editar_evidencia.html', evidencia=evidencia)


# --- ELIMINAR ---
@bp.route('/eliminar/<int:id>')
@login_required
def eliminar_evidencia(id):
    evidencia = Evidencia.query.get_or_404(id)
    if evidencia.aprendiz_id_aprendiz != current_user.id_aprendiz:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('evidencia_bp.mis_evidencias'))
    try:
        if evidencia.url_archivo and os.path.exists(evidencia.url_archivo):
            os.remove(evidencia.url_archivo)
    except Exception:
        pass
    db.session.delete(evidencia)
    db.session.commit()
    flash('Evidencia eliminada correctamente ✅', 'success')
    return redirect(url_for('evidencia_bp.mis_evidencias'))
