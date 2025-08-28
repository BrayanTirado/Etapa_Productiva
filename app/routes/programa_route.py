from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.users import Programa, Aprendiz, Instructor
from app import db

bp = Blueprint('programa_bp', __name__, url_prefix='/programa')


# --- FUNCIONES AUX ---
def enum_choices(model, column_name: str):
    """Devuelve las opciones válidas de un campo Enum de un modelo SQLAlchemy"""
    return model.__table__.c[column_name].type.enums


# --- LISTAR ---
@bp.route('/')
def listar_programas():
    programas = Programa.query.all()
    return render_template('programa/listar_programa.html', programas=programas)


# --- CREAR ---
@bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_programa():
    titulo_ops = enum_choices(Programa, 'titulo')
    jornada_ops = enum_choices(Programa, 'jornada')
    centro_ops = enum_choices(Programa, 'centro_formacion')

    if request.method == 'POST':
        nombre = request.form.get('nombre_programa', '').strip()
        titulo = request.form.get('titulo')
        jornada = request.form.get('jornada')
        centro = request.form.get('centro_formacion')

        # Validación básica
        if not nombre:
            flash("El nombre del programa es obligatorio.", "warning")
            return render_template('programa/nuevo_programa.html',
                                   titulo=titulo_ops, jornada=jornada_ops, centro_formacion=centro_ops)

        if titulo not in titulo_ops or jornada not in jornada_ops or centro not in centro_ops:
            flash("Selecciona valores válidos para Título, Jornada y Centro de formación.", "danger")
            return render_template('programa/nuevo_programa.html',
                                   titulo=titulo_ops, jornada=jornada_ops, centro_formacion=centro_ops)

        try:
            nuevo = Programa(
                nombre_programa=nombre,
                titulo=titulo,
                jornada=jornada,
                centro_formacion=centro
                # No seteamos FK explícitamente; serán None y ahora es allowed
            )
            db.session.add(nuevo)
            db.session.commit()

            # Mensaje de éxito y redirección
            flash("Programa guardado con éxito ✅", "success")
            return redirect(url_for('programa_bp.listar_programas'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar programa: {e}", "danger")

    return render_template('programa/nuevo_programa.html',
                           titulo=titulo_ops, jornada=jornada_ops, centro_formacion=centro_ops)


# --- EDITAR ---
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_programa(id):
    programa = Programa.query.get_or_404(id)
    titulo_ops = enum_choices(Programa, 'titulo')
    jornada_ops = enum_choices(Programa, 'jornada')
    centro_ops = enum_choices(Programa, 'centro_formacion')

    if request.method == 'POST':
        nombre = request.form.get('nombre_programa', '').strip()
        titulo = request.form.get('titulo')
        jornada = request.form.get('jornada')
        centro = request.form.get('centro_formacion')

        if not nombre:
            flash("El nombre del programa es obligatorio.", "warning")
            return render_template('programa/editar_programa.html',
                                   programa=programa, titulo=titulo_ops, jornada=jornada_ops,
                                   centro_formacion=centro_ops)

        if titulo not in titulo_ops or jornada not in jornada_ops or centro not in centro_ops:
            flash("Selecciona valores válidos para Título, Jornada y Centro de formación.", "danger")
            return render_template('programa/editar_programa.html',
                                   programa=programa, titulo=titulo_ops, jornada=jornada_ops,
                                   centro_formacion=centro_ops)

        try:
            programa.nombre_programa = nombre
            programa.titulo = titulo
            programa.jornada = jornada
            programa.centro_formacion = centro

            db.session.commit()
            flash("Programa actualizado correctamente ✅", "success")
            return redirect(url_for('programa_bp.listar_programas'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar programa: {e}", "danger")

    return render_template('programa/editar_programa.html',
                           programa=programa, titulo=titulo_ops, jornada=jornada_ops,
                           centro_formacion=centro_ops)


# --- ELIMINAR ---
@bp.route('/eliminar/<int:id>')
def eliminar_programa(id):
    programa = Programa.query.get_or_404(id)
    try:
        db.session.delete(programa)
        db.session.commit()
        flash("Programa eliminado correctamente ✅", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar programa: {e}", "danger")

    return redirect(url_for('programa_bp.listar_programas'))