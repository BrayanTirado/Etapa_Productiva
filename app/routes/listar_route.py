from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from app import db
from app.models.users import Aprendiz, Instructor

# Definición del Blueprint
estudiantes_bp = Blueprint('estudiantes', __name__, url_prefix='/estudiantes')

@estudiantes_bp.route('/listarEstudiantes', methods=['GET'])
@login_required
def listar_estudiantes():
    # Obtener filtro de documento
    documento = request.args.get('documento', type=str)

    # Lista vacía por defecto
    estudiantes = []

    # Solo si el usuario es Instructor
    if isinstance(current_user, Instructor):
        query = Aprendiz.query.filter(Aprendiz.instructor_id == current_user.id_instructor)

        # Filtrar por documento si se proporcionó
        if documento:
            query = query.filter(Aprendiz.documento.contains(documento))

        estudiantes = query.all()
        if estudiantes:
            flash(f'Mostrando aprendices asignados al instructor.', 'info')
        else:
            flash(f'No se encontraron aprendices asignados.', 'warning')
    else:
        flash('No tienes permiso para ver aprendices.', 'danger')

    # Respuesta para AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([
            {
                'nombre': e.nombre,
                'apellido': e.apellido,
                'tipo_documento': e.tipo_documento,
                'documento': e.documento,
                'email': e.email,
                'celular': e.celular,
                'ficha': e.ficha,
                'contrato_id': e.contrato_id
            }
            for e in estudiantes
        ])

    # Respuesta para render normal
    return render_template('listar.html', estudiantes=estudiantes, documento=documento)
