from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.users import Programa, Aprendiz, Instructor
from app import db

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
                           aprendiz_id=aprendiz_id)

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
        ficha = request.form.get('ficha', type=int)

        if not nombre:
            flash("El nombre del programa es obligatorio.", "warning")
            return render_template('programa/nuevo_programa.html',
                                   titulo=titulo_ops, jornada=jornada_ops, ficha=ficha)

        if titulo not in titulo_ops or jornada not in jornada_ops:
            flash("Selecciona valores válidos para Título, Jornada y Centro de formación.", "danger")
            return render_template('programa/nuevo_programa.html',
                                   titulo=titulo_ops, jornada=jornada_ops, ficha=ficha)

        try:
            programa = Programa.query.filter_by(
                nombre_programa=nombre,
                ficha=ficha,
                jornada=jornada
            ).first()

            if not programa:
                programa = Programa(
                    nombre_programa=nombre,
                    titulo=titulo,
                    jornada=jornada,
                    ficha=ficha,
                    instructor_id_instructor=current_user.id_instructor if isinstance(current_user, Instructor) else None
                )
                db.session.add(programa)
                db.session.flush()

            if isinstance(current_user, Aprendiz):
                current_user.programa = programa

            db.session.commit()
            flash("Programa registrado correctamente ✅", "success")
            return redirect(url_for('programa_bp.listar_programas', aprendiz_id=getattr(current_user, 'id_aprendiz', None)))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar programa: {e}", "danger")

    return render_template('programa/nuevo_programa.html',
                           titulo=titulo_ops, jornada=jornada_ops, ficha=None)

# --- EDITAR PROGRAMA ---
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_programa(id):
    programa = Programa.query.get_or_404(id)
    titulo_ops = enum_choices(Programa, 'titulo')
    jornada_ops = enum_choices(Programa, 'jornada')

    if not (isinstance(current_user, Aprendiz) and current_user.programa == programa):
        flash("No tienes permisos para editar este programa ❌", "danger")
        aprendiz_id = getattr(programa.aprendices_rel[0], 'id_aprendiz', None) if programa.aprendices_rel else None
        return redirect(url_for('programa_bp.listar_programas', aprendiz_id=aprendiz_id))

    if request.method == 'POST':
        nombre = request.form.get('nombre_programa', '').strip()
        titulo = request.form.get('titulo')
        jornada = request.form.get('jornada')
        ficha = request.form.get('ficha', type=int)

        if not nombre:
            flash("El nombre del programa es obligatorio.", "warning")
            return render_template('programa/editar_programa.html',
                                   programa=programa, titulo=titulo_ops, jornada=jornada_ops, ficha=ficha)

        if titulo not in titulo_ops or jornada not in jornada_ops or not ficha:
            flash("Selecciona valores válidos para Título, Jornada y Centro de formación.", "danger")
            return render_template('programa/editar_programa.html',
                                   programa=programa, titulo=titulo_ops, jornada=jornada_ops, ficha=ficha)

        try:
            programa.nombre_programa = nombre
            programa.titulo = titulo
            programa.jornada = jornada
            programa.ficha = ficha

            db.session.commit()
            flash("Programa actualizado correctamente ✅", "success")
            return redirect(url_for('programa_bp.listar_programas', aprendiz_id=getattr(current_user, 'id_aprendiz', None)))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar programa: {e}", "danger")

    return render_template('programa/editar_programa.html',
                           programa=programa, titulo=titulo_ops, jornada=jornada_ops, ficha=programa.ficha)

# --- ELIMINAR PROGRAMA ---
@bp.route('/eliminar/<int:id>')
@login_required
def eliminar_programa(id):
    programa = Programa.query.get_or_404(id)

    if not (isinstance(current_user, Aprendiz) and current_user.programa == programa):
        flash("No tienes permisos para eliminar este programa ❌", "danger")
        aprendiz_id = getattr(programa.aprendices_rel[0], 'id_aprendiz', None) if programa.aprendices_rel else None
        return redirect(url_for('programa_bp.listar_programas', aprendiz_id=aprendiz_id))

    try:
        db.session.delete(programa)
        db.session.commit()
        flash("Programa eliminado correctamente ✅", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar programa: {e}", "danger")

    return redirect(url_for('programa_bp.listar_programas', aprendiz_id=getattr(current_user, 'id_aprendiz', None)))
