from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.users import Aprendiz, Evidencia, Programa, Instructor
from app import db
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import date

# Blueprint para todas las rutas relacionadas con Aprendiz
bp = Blueprint('aprendiz_bp', __name__, url_prefix='/aprendiz')


# ---- CREAR NUEVO APRENDIZ ----
@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_aprendiz():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento')
        email = request.form.get('email')
        celular = request.form.get('celular')
        password_aprendiz = request.form.get('password_aprendiz')

        if not all([nombre, apellido, tipo_documento, documento, email, celular, password_aprendiz]):
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('aprendiz_bp.nuevo_aprendiz'))

        hashed_password = generate_password_hash(password_aprendiz)
        nuevo = Aprendiz(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=tipo_documento,
            documento=documento,
            email=email,
            celular=celular,
            password_aprendiz=hashed_password
        )
        try:
            db.session.add(nuevo)
            db.session.commit()
            flash('Aprendiz creado exitosamente.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un aprendiz con ese documento, correo o celular.', 'danger')
            return redirect(url_for('aprendiz_bp.nuevo_aprendiz'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el aprendiz: {str(e)}', 'danger')
            return redirect(url_for('aprendiz_bp.nuevo_aprendiz'))

    return render_template('aprendiz/nuevo.html')


# ---- EDITAR APRENDIZ ----
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_aprendiz(id):
    aprendiz = Aprendiz.query.get_or_404(id)

    if not (hasattr(current_user, 'id_aprendiz') and current_user.id_aprendiz == id) and not hasattr(current_user, 'id_instructor'):
        flash('No tienes permiso para editar este perfil.', 'danger')
        return redirect(url_for('auth.dashboard'))

    tipos_documento = [
        'Cedula de Ciudadania',
        'Tarjeta de Identidad',
        'Cedula Extrangera',
        'Registro Civil'
    ]

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        tipo_documento = request.form.get('tipo_documento')
        documento = request.form.get('documento', '').strip()
        email = request.form.get('email', '').strip()
        celular = request.form.get('celular', '').strip()
        password_aprendiz = request.form.get('password_aprendiz', '').strip()

        if not all([nombre, apellido, tipo_documento, documento, email, celular]):
            flash('Faltan campos obligatorios.', 'warning')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

        if tipo_documento not in tipos_documento:
            flash('Valor de tipo de documento inválido.', 'danger')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

        aprendiz.nombre = nombre
        aprendiz.apellido = apellido
        aprendiz.tipo_documento = tipo_documento
        aprendiz.documento = documento
        aprendiz.email = email
        aprendiz.celular = celular

        if password_aprendiz:
            aprendiz.password_aprendiz = generate_password_hash(password_aprendiz)

        try:
            db.session.commit()
            flash('Aprendiz actualizado correctamente.', 'success')
            return redirect(url_for('aprendiz_bp.perfil', id=id if hasattr(current_user, 'id_instructor') else None))
        except IntegrityError:
            db.session.rollback()
            flash('Documento, email o celular duplicado.', 'danger')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('aprendiz_bp.editar_aprendiz', id=id))

    return render_template(
        'perfil_aprendiz.html',
        aprendiz=aprendiz,
        mode='edit',
        tipos_documento=tipos_documento,
        es_aprendiz=(hasattr(current_user, 'id_aprendiz') and current_user.id_aprendiz == id),
        aprendiz_id=id if hasattr(current_user, 'id_instructor') else None
    )


# ---- ELIMINAR APRENDIZ ----
@bp.route('/eliminar/<int:id>')
@login_required
def eliminar_aprendiz(id):
    aprendiz = Aprendiz.query.get_or_404(id)

    if not hasattr(current_user, 'id_instructor'):
        flash('No tienes permiso para eliminar aprendices.', 'danger')
        return redirect(url_for('auth.dashboard'))

    try:
        db.session.delete(aprendiz)
        db.session.commit()
        flash('Aprendiz eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('aprendiz_bp.listar_aprendices'))


# ---- PERFIL DEL PROPIO APRENDIZ O VISTO POR INSTRUCTOR ----
@bp.route('/perfil', defaults={'id': None}, endpoint='perfil')
@bp.route('/perfil/<int:id>', endpoint='perfil')
@login_required
def perfil_aprendiz(id):
    aprendiz = None
    aprendiz_id = None
    es_aprendiz = False
    es_instructor = hasattr(current_user, 'id_instructor')

    progreso = None
    progreso_tiempo = None
    contrato = None
    mostrar_progreso = False
    mostrar_contrato = False

    # Caso: el aprendiz entra a su propio perfil
    if isinstance(current_user, Aprendiz) and id is None:
        aprendiz = current_user
        aprendiz_id = current_user.id_aprendiz
        es_aprendiz = True

    # Caso: instructor ve el perfil de un aprendiz
    elif isinstance(current_user, Instructor):
        aprendiz_id = id or request.args.get('aprendiz_id', type=int)
        if aprendiz_id:
            aprendiz = Aprendiz.query.get_or_404(aprendiz_id)
        else:
            flash('Selecciona un aprendiz para ver su perfil.', 'warning')
            return redirect(url_for('aprendiz_bp.listar_aprendices'))
    else:
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('auth.dashboard'))

    if aprendiz:
        # --- Calcular progreso evidencias ---
        total_requerido = 17
        evidencias_subidas = len(aprendiz.evidencias)
        progreso = int((evidencias_subidas / total_requerido) * 100) if total_requerido > 0 else 0

        # --- Calcular progreso tiempo contrato ---
        contrato_obj = aprendiz.contrato
        if contrato_obj and contrato_obj.fecha_inicio and contrato_obj.fecha_fin:
            fecha_inicio = contrato_obj.fecha_inicio.date() if hasattr(contrato_obj.fecha_inicio, "date") else contrato_obj.fecha_inicio
            fecha_fin = contrato_obj.fecha_fin.date() if hasattr(contrato_obj.fecha_fin, "date") else contrato_obj.fecha_fin

            total_dias = (fecha_fin - fecha_inicio).days
            dias_transcurridos = (date.today() - fecha_inicio).days
            if total_dias > 0:
                progreso_tiempo = round((dias_transcurridos / total_dias) * 100, 2)
                progreso_tiempo = min(max(progreso_tiempo, 0), 100)

            contrato = {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }

        mostrar_progreso = True
        mostrar_contrato = bool(contrato)

    return render_template(
        'perfil_aprendiz.html',
        aprendiz=aprendiz,
        es_aprendiz=es_aprendiz,
        es_instructor=es_instructor,
        mode='view',
        aprendiz_id=aprendiz_id,
        progreso=progreso,
        progreso_tiempo=progreso_tiempo,
        contrato=contrato,
        mostrar_progreso=mostrar_progreso,
        mostrar_contrato=mostrar_contrato
    )


# ---- VER PROCESO DE UN APRENDIZ (SOLO INSTRUCTOR) ----
@bp.route('/ver/<int:id>', methods=['GET'])
@login_required
def ver_aprendiz(id):
    if not hasattr(current_user, 'id_instructor'):
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('auth.dashboard'))

    aprendiz = Aprendiz.query.get_or_404(id)
    total_requerido = 17
    evidencias_subidas = len(aprendiz.evidencias)
    progreso = int((evidencias_subidas / total_requerido) * 100) if total_requerido > 0 else 0

    contrato_obj = aprendiz.contrato
    progreso_tiempo = 0
    contrato = None
    if contrato_obj and contrato_obj.fecha_inicio and contrato_obj.fecha_fin:
        fecha_inicio = contrato_obj.fecha_inicio.date() if hasattr(contrato_obj.fecha_inicio, "date") else contrato_obj.fecha_inicio
        fecha_fin = contrato_obj.fecha_fin.date() if hasattr(contrato_obj.fecha_fin, "date") else contrato_obj.fecha_fin

        total_dias = (fecha_fin - fecha_inicio).days
        dias_transcurridos = (date.today() - fecha_inicio).days
        if total_dias > 0:
            progreso_tiempo = round((dias_transcurridos / total_dias) * 100, 2)
            if progreso_tiempo < 0:
                progreso_tiempo = 0
            elif progreso_tiempo > 100:
                progreso_tiempo = 100

        contrato = {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }

    return render_template(
        'perfil_aprendiz.html',
        aprendiz=aprendiz,
        progreso=progreso,
        progreso_tiempo=progreso_tiempo,
        contrato=contrato,
        es_aprendiz=False,
        es_instructor=True,
        mode='view',
        mostrar_progreso=True,
        mostrar_contrato=bool(contrato),
        aprendiz_id=id
    )


# ---- LISTAR APRENDICES ----
@bp.route('/listar', methods=['GET'])
@login_required
def listar_aprendices():
    if not hasattr(current_user, 'id_instructor'):
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('auth.dashboard'))

    ficha_busqueda = request.args.get('ficha', type=int)
    if ficha_busqueda:
        aprendices = Aprendiz.query.filter(Aprendiz.programa.has(ficha=ficha_busqueda)).all()
        if aprendices:
            flash(f'Mostrando aprendices con ficha {ficha_busqueda}.', 'info')
        else:
            flash(f'No se encontraron aprendices para la ficha {ficha_busqueda}.', 'warning')
    else:
        aprendices = Aprendiz.query.all()

    return render_template('listar.html', aprendices=aprendices, ficha_seleccionada=ficha_busqueda)


# ---- DASHBOARD DE UN APRENDIZ (SOLO INSTRUCTOR) ----
@bp.route('/dashboard/<int:id>', methods=['GET'])
@login_required
def ver_dashboard_aprendiz(id):
    if not hasattr(current_user, 'id_instructor'):
        flash('No tienes permiso para ver el proceso de un aprendiz.', 'danger')
        return redirect(url_for('auth.dashboard'))

    aprendiz = Aprendiz.query.get_or_404(id)
    total_requerido = 17
    evidencias_subidas = len(aprendiz.evidencias)
    progreso = int((evidencias_subidas / total_requerido) * 100) if total_requerido > 0 else 0
    contrato = aprendiz.contrato

    progreso_tiempo = 0
    if contrato and contrato.fecha_inicio and contrato.fecha_fin:
        total_dias = (contrato.fecha_fin - contrato.fecha_inicio).days
        dias_transcurridos = (date.today() - contrato.fecha_inicio).days
        if total_dias > 0:
            progreso_tiempo = round((dias_transcurridos / total_dias) * 100, 2)
            progreso_tiempo = min(max(progreso_tiempo, 0), 100)

    return render_template(
        'dasboardh_aprendiz.html',
        aprendiz=aprendiz,
        progreso=progreso,
        progreso_tiempo=progreso_tiempo,
        contrato=contrato,
        ocultar_notificaciones=True  # <-- nueva variable
    )

