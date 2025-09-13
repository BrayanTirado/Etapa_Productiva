from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from app import db
from app.models.users import Aprendiz, Instructor
from datetime import datetime

# Definición del Blueprint
estudiantes_bp = Blueprint('estudiantes', __name__, url_prefix='/estudiantes')

from flask import jsonify

@estudiantes_bp.route('/listarEstudiantes', methods=['GET'])
@login_required
def listar_estudiantes():
    # Obtener filtros de la URL
    documento = request.args.get('documento', type=str)
    nombre = request.args.get('nombre', type=str)
    apellido = request.args.get('apellido', type=str)

    estudiantes = []

    # Solo si el usuario es Instructor
    if isinstance(current_user, Instructor):
        query = Aprendiz.query.filter(Aprendiz.instructor_id == current_user.id_instructor)

        # Aplicar filtros si se proporcionaron
        if documento:
            query = query.filter(Aprendiz.documento.contains(documento))
        if nombre:
            query = query.filter(Aprendiz.nombre.contains(nombre))
        if apellido:
            query = query.filter(Aprendiz.apellido.contains(apellido))

        estudiantes = query.all()

        if not estudiantes:
            flash('No se encontraron aprendices asignados.', 'warning')
    
    else:
        # Si el usuario no es instructor
        flash('No tienes permiso para ver aprendices.', 'danger')

    # Respuesta para AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([
            {
                'nombre': e.nombre,
                'apellido': e.apellido,
                'tipo_documento': e.tipo_documento,
                'documento': e.documento,
                'correo': e.correo,
                'celular': e.celular,
                'ficha': getattr(e, 'ficha', None),
                'contrato_id': getattr(e, 'contrato_id', None)
            }
            for e in estudiantes
        ])

    # Respuesta para render normal
    return render_template('listar.html', estudiantes=estudiantes, documento=documento, nombre=nombre, apellido=apellido, now=datetime.now())
