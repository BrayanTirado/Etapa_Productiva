from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
from app.models.users import Evidencia, Aprendiz, Instructor
from app import db
import os
from werkzeug.utils import secure_filename
from datetime import date, datetime, timedelta
from uuid import uuid4
from sqlalchemy import text

bp = Blueprint('evidencia_bp', __name__, url_prefix='/evidencia')

# --- VERIFICAR RESTRICCIÓN ANTES DE SUBIR ---
@bp.route('/verificar_restriccion', methods=['POST'])
@login_required
def verificar_restriccion():
    """Verifica si hay restricción de tiempo para un tipo de archivo específico."""
    if not isinstance(current_user, Aprendiz):
        return {'error': 'Acceso denegado'}, 403

    tipo = request.form.get('tipo')
    sesion_excel = request.form.get('sesion_excel')

    if not tipo:
        return {'error': 'Tipo no especificado'}, 400

    # Verificar restricciones temporales
    print(f"DEBUG: Verificando restricción para tipo={tipo}, sesion_excel={sesion_excel}")
    puede_subir, mensaje_error, fecha_proxima = puede_subir_archivo(
        current_user.id_aprendiz, tipo, sesion_excel
    )
    print(f"DEBUG: Resultado - puede_subir={puede_subir}, mensaje={mensaje_error}, fecha_proxima={fecha_proxima}")

    return {
        'restringido': not puede_subir,
        'mensaje': mensaje_error,
        'fecha_proxima': fecha_proxima
    }

# --- MIGRACIÓN PARA AGREGAR CAMPO SESION_EXCEL ---
@bp.route('/migrar_sesion_excel')
@login_required
def migrar_sesion_excel():
    """Migra las evidencias existentes para asignar el campo sesion_excel correctamente."""
    if not isinstance(current_user, Aprendiz):
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('auth.dashboard'))

    try:
        # Buscar evidencias Excel que no tienen sesion_excel asignado
        evidencias_sin_sesion = Evidencia.query.filter_by(
            tipo='Excel',
            sesion_excel=None
        ).all()

        actualizadas = 0
        for evidencia in evidencias_sin_sesion:
            # Si tiene primera_subida_excel_15, asignar '15_dias'
            if evidencia.primera_subida_excel_15:
                evidencia.sesion_excel = '15_dias'
                actualizadas += 1
            # Si tiene primera_subida_excel_3, asignar '3_meses'
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

def puede_subir_archivo(aprendiz_id: int, tipo: str, sesion_excel: str = None) -> tuple[bool, str, str]:
    """
    Verifica si un aprendiz puede subir un archivo según las restricciones temporales.
    Retorna (puede_subir, mensaje_error, fecha_proxima)
    """
    from app.models.users import Evidencia

    hoy = date.today()

    # Buscar la primera subida del tipo de archivo
    if tipo == 'word':
        primera_subida = db.session.query(Evidencia.primera_subida_word)\
            .filter_by(aprendiz_id_aprendiz=aprendiz_id)\
            .filter(Evidencia.primera_subida_word.isnot(None))\
            .order_by(Evidencia.primera_subida_word)\
            .first()
        if primera_subida and primera_subida[0]:
            dias_desde_primera = (hoy - primera_subida[0]).days
            if dias_desde_primera < 90:  # 3 meses
                dias_restantes = 90 - dias_desde_primera
                fecha_proxima = primera_subida[0] + timedelta(days=90)
                return False, f"No puedes subir otro archivo Word. Debes esperar {dias_restantes} días más.", fecha_proxima.strftime('%d/%m/%Y')

    elif tipo == 'excel':
        print(f"DEBUG: Verificando restricción Excel para sesión: {sesion_excel}")

        if sesion_excel == '15_dias':
            print(f"DEBUG: Aplicando lógica de 15 días")
            # Buscar la primera subida de Excel 15 días (ordenada por fecha más antigua)
            primera_subida = db.session.query(Evidencia.primera_subida_excel_15)\
                .filter_by(aprendiz_id_aprendiz=aprendiz_id)\
                .filter(Evidencia.primera_subida_excel_15.isnot(None))\
                .order_by(Evidencia.primera_subida_excel_15)\
                .first()
            print(f"DEBUG: Primera subida Excel 15 días encontrada: {primera_subida}")

            # Si no hay registro de primera subida, buscar la evidencia más antigua de Excel 15 días
            if not primera_subida or not primera_subida[0]:
                evidencia_mas_antigua = db.session.query(db.func.min(Evidencia.fecha_subida))\
                    .filter_by(aprendiz_id_aprendiz=aprendiz_id, tipo='Excel', sesion_excel='15_dias')\
                    .filter(Evidencia.fecha_subida.isnot(None))\
                    .first()
                print(f"DEBUG: Evidencia más antigua Excel 15 días: {evidencia_mas_antigua}")
                if evidencia_mas_antigua and evidencia_mas_antigua[0]:
                    primera_subida = (evidencia_mas_antigua[0],)
                    print(f"DEBUG: Usando fecha de evidencia más antigua: {primera_subida[0]}")

            if primera_subida and primera_subida[0]:
                dias_desde_primera = (hoy - primera_subida[0]).days
                print(f"DEBUG: Días desde primera subida Excel 15 días: {dias_desde_primera}")
                if dias_desde_primera < 90:
                    dias_restantes = 90 - dias_desde_primera
                    fecha_proxima = primera_subida[0] + timedelta(days=90)
                    return False, f"No puedes subir otro archivo Excel (sesión 15 días). Debes esperar {dias_restantes} días más.", fecha_proxima.strftime('%d/%m/%Y')
        elif sesion_excel == '3_meses':
            print(f"DEBUG: Aplicando lógica de 3 meses")
            # Buscar la primera subida de Excel 3 meses (ordenada por fecha más antigua)
            primera_subida = db.session.query(Evidencia.primera_subida_excel_3)\
                .filter_by(aprendiz_id_aprendiz=aprendiz_id)\
                .filter(Evidencia.primera_subida_excel_3.isnot(None))\
                .order_by(Evidencia.primera_subida_excel_3)\
                .first()
            print(f"DEBUG: Primera subida Excel 3 meses encontrada: {primera_subida}")

            # Si no hay registro de primera subida, buscar la evidencia más antigua de Excel 3 meses
            if not primera_subida or not primera_subida[0]:
                evidencia_mas_antigua = db.session.query(db.func.min(Evidencia.fecha_subida))\
                    .filter_by(aprendiz_id_aprendiz=aprendiz_id, tipo='Excel', sesion_excel='3_meses')\
                    .filter(Evidencia.fecha_subida.isnot(None))\
                    .first()
                print(f"DEBUG: Evidencia más antigua Excel 3 meses: {evidencia_mas_antigua}")
                if evidencia_mas_antigua and evidencia_mas_antigua[0]:
                    primera_subida = (evidencia_mas_antigua[0],)
                    print(f"DEBUG: Usando fecha de evidencia más antigua: {primera_subida[0]}")

            if primera_subida and primera_subida[0]:
                dias_desde_primera = (hoy - primera_subida[0]).days
                print(f"DEBUG: Días desde primera subida Excel 3 meses: {dias_desde_primera}")
                if dias_desde_primera < 90:
                    dias_restantes = 90 - dias_desde_primera
                    fecha_proxima = primera_subida[0] + timedelta(days=90)
                    return False, f"No puedes subir otro archivo Excel (sesión 3 meses). Debes esperar {dias_restantes} días más.", fecha_proxima.strftime('%d/%m/%Y')
            else:
                print(f"DEBUG: No se encontró primera subida para Excel 3 meses, permitiendo subida")
        else:
            print(f"DEBUG: Sesión Excel no reconocida: {sesion_excel}, permitiendo subida")


    print(f"DEBUG: No se aplicó ninguna restricción para tipo={tipo}, sesion_excel={sesion_excel}, permitiendo subida")
    return True, "", ""

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
    evidencias_excel_15 = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Excel', sesion_excel='15_dias').all()
    evidencias_excel_3 = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Excel', sesion_excel='3_meses').all()
    evidencias_pdf = Evidencia.query.filter_by(aprendiz_id_aprendiz=aprendiz.id_aprendiz, tipo='Pdf').all()

    # Debug: imprimir información sobre las evidencias Excel
    print(f"DEBUG: Total evidencias Excel encontradas: {len(evidencias_excel_15) + len(evidencias_excel_3)}")
    print(f"DEBUG: Evidencias Excel 15 días: {len(evidencias_excel_15)}")
    for ev in evidencias_excel_15:
        print(f"  - ID: {ev.id_evidencia}, Sesión: {ev.sesion_excel}, Archivo: {ev.nombre_archivo}")
    print(f"DEBUG: Evidencias Excel 3 meses: {len(evidencias_excel_3)}")
    for ev in evidencias_excel_3:
        print(f"  - ID: {ev.id_evidencia}, Sesión: {ev.sesion_excel}, Archivo: {ev.nombre_archivo}")

    return render_template('evidencia/listar_evidencia.html',
                            aprendiz=aprendiz,
                            evidencias_word=evidencias_word,
                            evidencias_excel_15=evidencias_excel_15,
                            evidencias_excel_3=evidencias_excel_3,
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
        # Verificar restricciones temporales para mostrar modal si es necesario
        if tipo == 'excel':
            sesion_excel = request.args.get('sesion_excel', '15_dias')
            puede_subir, mensaje_error, fecha_proxima = puede_subir_archivo(current_user.id_aprendiz, tipo, sesion_excel)
        else:
            puede_subir, mensaje_error, fecha_proxima = puede_subir_archivo(current_user.id_aprendiz, tipo)

        if not puede_subir:
            # Mostrar modal de restricción inmediatamente
            return render_template('evidencia/choose_type.html',
                                  error_restriccion=True,
                                  mensaje_error=mensaje_error,
                                  fecha_proxima=fecha_proxima,
                                  now=datetime.now())

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

    # Verificar restricciones temporales
    if tipo == 'excel':
        # Para Excel necesitamos saber qué sesión es
        sesion_excel = request.form.get('sesion_excel', '15_dias')
        print(f"DEBUG: Form data - sesion_excel: {sesion_excel}")  # Debug adicional
        print(f"DEBUG: All form data: {dict(request.form)}")  # Debug adicional
        puede_subir, mensaje_error, fecha_proxima = puede_subir_archivo(current_user.id_aprendiz, tipo, sesion_excel)
    else:
        puede_subir, mensaje_error, fecha_proxima = puede_subir_archivo(current_user.id_aprendiz, tipo)

    if not puede_subir:
        # En lugar de redirigir, mostrar modal informativo
        return render_template('evidencia/choose_type.html',
                             error_restriccion=True,
                             mensaje_error=mensaje_error,
                             fecha_proxima=fecha_proxima,
                             now=datetime.now())

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

    # Actualizar campos de control de tiempo si es la primera subida
    hoy = date.today()
    print(f"DEBUG: Actualizando campos de control de tiempo para tipo={tipo}, hoy={hoy}")

    if tipo == 'word':
        # Buscar primera_subida_word existente
        existing_word = db.session.query(Evidencia.primera_subida_word)\
            .filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz)\
            .filter(Evidencia.primera_subida_word.isnot(None))\
            .first()
        if existing_word:
            evidencia.primera_subida_word = existing_word[0]
        else:
            evidencia.primera_subida_word = hoy
        print(f"DEBUG: primera_subida_word establecido a {evidencia.primera_subida_word}")
    elif tipo == 'excel':
        sesion_excel = request.form.get('sesion_excel', '15_dias')
        print(f"DEBUG: Sesión Excel seleccionada: {sesion_excel}")  # Debug

        # Guardar la sesión específica en el campo sesion_excel
        evidencia.sesion_excel = sesion_excel
        print(f"DEBUG: Asignando sesion_excel = {evidencia.sesion_excel}")  # Debug

        if sesion_excel == '15_dias':
            # Buscar primera_subida_excel_15 existente
            existing_15 = db.session.query(Evidencia.primera_subida_excel_15)\
                .filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz)\
                .filter(Evidencia.primera_subida_excel_15.isnot(None))\
                .first()
            if existing_15:
                evidencia.primera_subida_excel_15 = existing_15[0]
            else:
                evidencia.primera_subida_excel_15 = hoy
            print(f"DEBUG: primera_subida_excel_15 establecido a {evidencia.primera_subida_excel_15}")
        elif sesion_excel == '3_meses':
            # Buscar primera_subida_excel_3 existente
            existing_3 = db.session.query(Evidencia.primera_subida_excel_3)\
                .filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz)\
                .filter(Evidencia.primera_subida_excel_3.isnot(None))\
                .first()
            if existing_3:
                evidencia.primera_subida_excel_3 = existing_3[0]
            else:
                evidencia.primera_subida_excel_3 = hoy
            print(f"DEBUG: primera_subida_excel_3 establecido a {evidencia.primera_subida_excel_3}")

    db.session.commit()

    # Crear notificación automática para el instructor
    from app.models.users import Notificacion
    try:
        # Obtener el instructor del aprendiz
        instructor = current_user.instructor
        if instructor:
            # Determinar el tipo de archivo para el mensaje
            tipo_archivo = tipo.capitalize()
            if tipo == 'excel':
                sesion_excel = request.form.get('sesion_excel', '15_dias')
                tipo_archivo = f"Excel ({'15 días' if sesion_excel == '15_dias' else '3 meses'})"

            # Crear notificación con motivo y mensaje separados
            motivo = "Nueva Evidencia subida"
            mensaje = f"El aprendiz {current_user.nombre} {current_user.apellido} ha Subido una nueva evidencia."

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
        # Si hay error en la notificación, no bloquear la subida de evidencia
        print(f"Error al crear notificación: {e}")
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
