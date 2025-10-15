from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.users import Programa, Aprendiz, Instructor, Ficha
from app import db
from datetime import datetime

bp = Blueprint('programa_bp', __name__, url_prefix='/programa')

# --- FUNCIONES AUX ---
def enum_choices(model, column_name: str):
    """Devuelve las opciones válidas de un campo Enum de un modelo SQLAlchemy"""
    col_type = model.__table__.c[column_name].type
    if hasattr(col_type, 'enums'):
        return col_type.enums
    return None

# --- LISTAR PROGRAMAS ---
@bp.route('/')
@login_required
def listar_programas():
    programas = []
    aprendiz_id = None

    if isinstance(current_user, Aprendiz):
        aprendiz_id = current_user.id_aprendiz
        if current_user.ficha:
            # Crear un objeto similar a programa para compatibilidad con el template
            programas = [{
                'id_programa': current_user.ficha.id_ficha,
                'nombre_programa': current_user.ficha.nombre_programa,
                'titulo': current_user.ficha.titulo,
                'jornada': current_user.ficha.jornada,
                'ficha': current_user.ficha.numero_ficha
            }]

    elif isinstance(current_user, Instructor):
        # Mostrar fichas solo de aprendices asignados a este instructor
        aprendiz_id_param = request.args.get('aprendiz_id', type=int)
        if aprendiz_id_param:
            aprendiz_id = aprendiz_id_param
            aprendiz = Aprendiz.query.filter_by(
                id_aprendiz=aprendiz_id,
                instructor_id=current_user.id_instructor
            ).first()
            if aprendiz and aprendiz.ficha:
                programas = [{
                    'id_programa': aprendiz.ficha.id_ficha,
                    'nombre_programa': aprendiz.ficha.nombre_programa,
                    'titulo': aprendiz.ficha.titulo,
                    'jornada': aprendiz.ficha.jornada,
                    'ficha': aprendiz.ficha.numero_ficha
                }]

    return render_template('programa/listar_programa.html',
                           programas=programas,
                           aprendiz_id=aprendiz_id,
                           now=datetime.now())

# --- CREAR PROGRAMA ---
@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_programa():
    titulo_ops = enum_choices(Programa, 'titulo')
    jornada_ops = enum_choices(Programa, 'jornada')

    if request.method == 'POST':
        nombre = request.form.get('nombre_programa', '').strip()
        titulo = request.form.get('titulo')
        jornada = request.form.get('jornada')
        numero_ficha = request.form.get('numero_ficha', type=int)

        if not nombre or not numero_ficha:
            flash("El nombre del programa y el número de ficha son obligatorios.", "warning")
            return render_template('programa/nuevo_programa.html',
                                   titulo=titulo_ops, jornada=jornada_ops, numero_ficha=numero_ficha, now=datetime.now())

        if titulo not in titulo_ops or jornada not in jornada_ops:
            flash("Selecciona valores válidos para Título y Jornada.", "danger")
            return render_template('programa/nuevo_programa.html',
                                   titulo=titulo_ops, jornada=jornada_ops, numero_ficha=numero_ficha, now=datetime.now())

        try:
            # Buscar ficha existente por número, si no existe crearla
            ficha = Ficha.query.filter_by(numero_ficha=numero_ficha).first()
            if not ficha:
                ficha = Ficha(
                    numero_ficha=numero_ficha,
                    nombre_programa=nombre,
                    titulo=titulo,
                    jornada=jornada
                )
                db.session.add(ficha)
                db.session.flush()

            # Asignar ficha al aprendiz
            if isinstance(current_user, Aprendiz):
                current_user.ficha = ficha

            db.session.commit()
            flash("Ficha registrada correctamente [OK]", "success")
            return redirect(url_for('programa_bp.listar_programas', aprendiz_id=getattr(current_user, 'id_aprendiz', None)))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar ficha: {e}", "danger")

    return render_template('programa/nuevo_programa.html',
                           titulo=titulo_ops, jornada=jornada_ops, numero_ficha=None, now=datetime.now())

# --- EDITAR FICHA ---
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_programa(id):
    ficha = Ficha.query.get_or_404(id)
    titulo_ops = enum_choices(Ficha, 'titulo')
    jornada_ops = enum_choices(Ficha, 'jornada')

    if not (isinstance(current_user, Aprendiz) and current_user.ficha == ficha):
        flash("No tienes permisos para editar esta ficha [ERROR]", "danger")
        aprendiz_id = getattr(current_user, 'id_aprendiz', None)
        return redirect(url_for('programa_bp.listar_programas', aprendiz_id=aprendiz_id))

    if request.method == 'POST':
        nombre = request.form.get('nombre_programa', '').strip()
        titulo = request.form.get('titulo')
        jornada = request.form.get('jornada')
        numero_ficha = request.form.get('numero_ficha', type=int)

        if not nombre or not numero_ficha:
            flash("El nombre del programa y el número de ficha son obligatorios.", "warning")
            return render_template('programa/editar_programa.html',
                                   ficha=ficha, titulo=titulo_ops, jornada=jornada_ops, numero_ficha=numero_ficha, now=datetime.now())

        if titulo not in titulo_ops or jornada not in jornada_ops:
            flash("Selecciona valores válidos para Título y Jornada.", "danger")
            return render_template('programa/editar_programa.html',
                                   ficha=ficha, titulo=titulo_ops, jornada=jornada_ops, numero_ficha=numero_ficha, now=datetime.now())

        try:
            ficha.nombre_programa = nombre
            ficha.titulo = titulo
            ficha.jornada = jornada
            ficha.numero_ficha = numero_ficha

            db.session.commit()
            flash("Ficha actualizada correctamente [OK]", "success")
            return redirect(url_for('programa_bp.listar_programas', aprendiz_id=getattr(current_user, 'id_aprendiz', None)))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar ficha: {e}", "danger")

    return render_template('programa/editar_programa.html',
                           ficha=ficha, titulo=titulo_ops, jornada=jornada_ops, numero_ficha=ficha.numero_ficha, now=datetime.now())

# --- ELIMINAR FICHA ---
@bp.route('/eliminar/<int:id>')
@login_required
def eliminar_programa(id):
    ficha = Ficha.query.get_or_404(id)

    if not (isinstance(current_user, Aprendiz) and current_user.ficha == ficha):
        flash("No tienes permisos para eliminar esta ficha [ERROR]", "danger")
        aprendiz_id = getattr(current_user, 'id_aprendiz', None)
        return redirect(url_for('programa_bp.listar_programas', aprendiz_id=aprendiz_id))

    try:
        # Desasignar ficha de todos los aprendices que la tienen
        Aprendiz.query.filter_by(ficha_id=ficha.id_ficha).update({'ficha_id': None})
        db.session.delete(ficha)
        db.session.commit()
        flash("Ficha eliminada correctamente [OK]", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar ficha: {e}", "danger")

    return redirect(url_for('programa_bp.listar_programas', aprendiz_id=getattr(current_user, 'id_aprendiz', None)))
