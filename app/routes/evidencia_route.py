from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.users import Evidencia
from app import db
import os
from werkzeug.utils import secure_filename
from datetime import datetime

bp = Blueprint('evidencia_bp', __name__, url_prefix='/evidencia')

# Carpeta donde se guardarán los archivos
UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@bp.route('/')
def listar_evidencias():
    evidencias = Evidencia.query.all()
    return render_template('evidencia/listar_evidencia.html', evidencias=evidencias)

@bp.route('/nueva', methods=['GET', 'POST'])
def nueva_evidencia():
    if request.method == 'POST':
        archivo = request.files.get('archivo')
        if archivo:
            filename = secure_filename(archivo.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            archivo.save(filepath)

            # Convertir la fecha de string a date
            fecha_subida = datetime.strptime(request.form['fecha_subida'], '%Y-%m-%d').date()

            nueva = Evidencia(
                formato=filename.split('.')[-1],  # toma la extensión como formato
                nombre_archivo=request.form['nombre_archivo'],
                url_archivo=filepath,
                fecha_subida=fecha_subida,
                aprendiz_id_aprendiz=int(request.form['aprendiz_id_aprendiz']),
                tipo=request.form['tipo']
            )
            db.session.add(nueva)
            db.session.commit()
            flash('Archivo subido correctamente.', 'success')
            return redirect(url_for('evidencia_bp.listar_evidencias'))
        else:
            flash('Debe seleccionar un archivo.', 'error')
            return redirect(request.url)

    return render_template('evidencia/nueva_evidencia.html')

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_evidencia(id):
    evidencia = Evidencia.query.get_or_404(id)
    if request.method == 'POST':
        evidencia.nombre_archivo = request.form['nombre_archivo']
        evidencia.tipo = request.form['tipo']
        evidencia.fecha_subida = datetime.strptime(request.form['fecha_subida'], '%Y-%m-%d').date()

        archivo = request.files.get('archivo')
        if archivo:
            filename = secure_filename(archivo.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            archivo.save(filepath)
            evidencia.url_archivo = filepath
            evidencia.formato = filename.split('.')[-1]

        db.session.commit()
        flash('Evidencia actualizada correctamente.', 'success')
        return redirect(url_for('evidencia_bp.listar_evidencias'))

    return render_template('evidencia/editar_evidencia.html', evidencia=evidencia)

@bp.route('/eliminar/<int:id>')
def eliminar_evidencia(id):
    evidencia = Evidencia.query.get_or_404(id)
    if os.path.exists(evidencia.url_archivo):
        os.remove(evidencia.url_archivo)
    db.session.delete(evidencia)
    db.session.commit()
    flash('Evidencia eliminada.', 'success')
    return redirect(url_for('evidencia_bp.listar_evidencias'))
