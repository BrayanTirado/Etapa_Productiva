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
        if current_user.programa:
            programas = [current_user.programa]

    elif isinstance(current_user, Instructor):
        # Mostrar programas solo de aprendices asignados a este instructor
        aprendiz_id_param = request.args.get('aprendiz_id', type=int)
        if aprendiz_id_param:
            aprendiz_id = aprendiz_id_param
            aprendiz = Aprendiz.query.filter_by(
                id_aprendiz=aprendiz_id,
                instructor_id=current_user.id_instructor
            ).first()
            if aprendiz and aprendiz.programa:
                programas = [aprendiz.programa]

    return render_template('programa/listar_programa.html',
                           programas=programas,
                           aprendiz_id=aprendiz_id,
                           now=datetime.now())

# --- CREAR PROGRAMA ---
@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_programa():
    titulo_ops = enum_choices(Programa, 'titulo')

    if request.method == 'POST':
        nombre = request.form.get('nombre_programa', '').strip()
        titulo = request.form.get('titulo')
        numero_ficha = request.form.get('numero_ficha', type=int)

        if not nombre or not numero_ficha:
            flash("El nombre del programa y el número de ficha son obligatorios.", "warning")
            return render_template('programa/nuevo_programa.html',
                                   titulo=titulo_ops, numero_ficha=numero_ficha, now=datetime.now())

        if titulo not in titulo_ops:
            flash("Selecciona un valor válido para Título.", "danger")
            return render_template('programa/nuevo_programa.html',
                                   titulo=titulo_ops, numero_ficha=numero_ficha, now=datetime.now())

        try:
            # Buscar ficha existente por número, si no existe crearla
            ficha = Ficha.query.filter_by(numero_ficha=numero_ficha).first()
            if not ficha:
                ficha = Ficha(numero_ficha=numero_ficha)
                db.session.add(ficha)
                db.session.flush()

            # Buscar programa existente con la misma ficha, nombre y titulo
            programa = Programa.query.filter_by(
                nombre_programa=nombre,
                titulo=titulo,
                ficha_id=ficha.id_ficha
            ).first()

            if not programa:
                programa = Programa(
                    nombre_programa=nombre,
                    titulo=titulo,
                    ficha_id=ficha.id_ficha
                )
                db.session.add(programa)
                db.session.flush()

            # Asignar programa al aprendiz
            if isinstance(current_user, Aprendiz):
                current_user.programa = programa

            db.session.commit()
            flash("Programa registrado correctamente [OK]", "success")
            return redirect(url_for('programa_bp.listar_programas', aprendiz_id=getattr(current_user, 'id_aprendiz', None)))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar programa: {e}", "danger")

    return render_template('programa/nuevo_programa.html',
                           titulo=titulo_ops, numero_ficha=None, now=datetime.now())

# --- EDITAR PROGRAMA ---
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_programa(id):
    programa = Programa.query.get_or_404(id)
    titulo_ops = enum_choices(Programa, 'titulo')

    if not (isinstance(current_user, Aprendiz) and current_user.programa == programa):
        flash("No tienes permisos para editar este programa [ERROR]", "danger")
        aprendiz_id = getattr(programa.aprendices_rel[0], 'id_aprendiz', None) if programa.aprendices_rel else None
        return redirect(url_for('programa_bp.listar_programas', aprendiz_id=aprendiz_id))

    if request.method == 'POST':
        # Jornada removida, no hay edición disponible
        flash("Edición no disponible.", "info")
        return redirect(url_for('programa_bp.listar_programas', aprendiz_id=getattr(current_user, 'id_aprendiz', None)))

    return render_template('programa/editar_programa.html',
                           programa=programa, titulo=titulo_ops, ficha=programa.ficha, now=datetime.now())

# --- ELIMINAR PROGRAMA ---
@bp.route('/eliminar/<int:id>')
@login_required
def eliminar_programa(id):
    programa = Programa.query.get_or_404(id)

    if not (isinstance(current_user, Aprendiz) and current_user.programa == programa):
        flash("No tienes permisos para eliminar este programa [ERROR]", "danger")
        aprendiz_id = getattr(programa.aprendices_rel[0], 'id_aprendiz', None) if programa.aprendices_rel else None
        return redirect(url_for('programa_bp.listar_programas', aprendiz_id=aprendiz_id))

    try:
        db.session.delete(programa)
        db.session.commit()
        flash("Programa eliminado correctamente [OK]", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar programa: {e}", "danger")

    return redirect(url_for('programa_bp.listar_programas', aprendiz_id=getattr(current_user, 'id_aprendiz', None)))
