from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required
from app import db
from app.models.users import Aprendiz

# Definición del Blueprint
estudiantes_bp = Blueprint('estudiantes', __name__, url_prefix='/estudiantes')

@estudiantes_bp.route('/listarEstudiantes', methods=['GET'])
@login_required
def listar_estudiantes():
    # Obtener filtro de ficha como número
    ficha = request.args.get('ficha', type=int)

    # Lista vacía por defecto
    estudiantes = []

    # Solo ejecutar la query si se proporciona una ficha
    if ficha is not None:
        query = Aprendiz.query.filter(Aprendiz.ficha == ficha)
        estudiantes = query.all()
        if estudiantes:
            flash(f'Mostrando aprendices con ficha {ficha}.', 'info')
        else:
            flash(f'No se encontraron aprendices para la ficha {ficha}.', 'warning')

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
                'contrato_id': e.contrato_id  # <-- corregido
            }
            for e in estudiantes
        ])

    # Respuesta para render normal
    return render_template('listar.html', estudiantes=estudiantes, ficha=ficha)
