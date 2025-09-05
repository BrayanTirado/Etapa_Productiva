from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.users import Empresa, Contrato, Aprendiz, Instructor
from app import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date
import calendar

bp = Blueprint('empresa_bp', __name__, url_prefix='/empresa')

def add_months(sourcedate: date, months: int) -> date:
    """
    Suma `months` meses a `sourcedate` cuidando los días de mes (ej: 31 ene -> 30 jun si aplica).
    Evita dependencia externa (dateutil).
    """
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


# --- LISTAR EMPRESAS ---
@bp.route('/')
@login_required
def listar_empresas():
    """
    Listar empresas según el usuario:
    - Aprendiz: solo su empresa y puede editar/eliminar.
    - Instructor: solo puede ver empresas de un aprendiz, no editar/eliminar.
    """
    aprendiz_id = None
    empresas = []

    es_aprendiz = hasattr(current_user, 'id_aprendiz')  # Detecta si es aprendiz
    es_instructor = isinstance(current_user, Instructor)

    if es_aprendiz:
        aprendiz_id = current_user.id_aprendiz
        empresas = Empresa.query.filter_by(aprendiz_id_aprendiz=aprendiz_id).all()
    elif es_instructor:
        aprendiz_id_param = request.args.get('aprendiz_id', type=int)
        if aprendiz_id_param:
            aprendiz_id = aprendiz_id_param
            empresas = Empresa.query.filter_by(aprendiz_id_aprendiz=aprendiz_id).all()

    return render_template(
        'empresa/listar_empresa.html',
        empresas=empresas,
        aprendiz_id=aprendiz_id,
        es_aprendiz=es_aprendiz  # <-- esta variable se usa en el template
    )


# --- CREAR EMPRESA ---
@bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_empresa():
    if hasattr(current_user, 'id_aprendiz') and Empresa.query.filter_by(aprendiz_id_aprendiz=current_user.id_aprendiz).first():
        flash('Ya tienes una empresa registrada. Contacta al instructor para cambios.', 'warning')
        return redirect(url_for('empresa_bp.listar_empresas', aprendiz_id=current_user.id_aprendiz))

    if request.method == 'POST':
        try:
            nueva = Empresa(
                nombre_empresa=request.form.get('nombre_empresa'),
                nit=request.form.get('nit'),
                direccion=request.form.get('direccion'),
                telefono=request.form.get('telefono'),
                correo_empresa=request.form.get('correo_empresa'),
                nombre_jefe=request.form.get('nombre_jefe'),
                correo_jefe=request.form.get('correo_jefe'),
                telefono_jefe=request.form.get('telefono_jefe'),
                aprendiz_id_aprendiz=current_user.id_aprendiz
            )
            db.session.add(nueva)
            db.session.flush()  # <-- aquí ya tenemos id_empresa disponible

            # Crear contrato si se ingresa fecha_inicio (ahora fecha_fin se calcula si no se envía)
            fecha_inicio_raw = request.form.get('fecha_inicio')
            fecha_fin_raw = request.form.get('fecha_fin')
            contrato_creado = None

            if fecha_inicio_raw:
                try:
                    fecha_inicio = datetime.strptime(fecha_inicio_raw, '%Y-%m-%d').date()
                except ValueError:
                    db.session.rollback()
                    flash('Formato de fecha de inicio inválido. Usa YYYY-MM-DD.', 'danger')
                    return redirect(url_for('empresa_bp.nueva_empresa'))

                # Si el frontend envía fecha_fin la usamos; si no, la calculamos +6 meses
                if fecha_fin_raw:
                    try:
                        fecha_fin = datetime.strptime(fecha_fin_raw, '%Y-%m-%d').date()
                    except ValueError:
                        db.session.rollback()
                        flash('Formato de fecha de fin inválido. Usa YYYY-MM-DD.', 'danger')
                        return redirect(url_for('empresa_bp.nueva_empresa'))
                else:
                    fecha_fin = add_months(fecha_inicio, 6)

                contrato_creado = Contrato(
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    tipo_contrato=request.form.get('tipo_contrato'),
                    empresa_id_empresa=nueva.id_empresa
                )
                db.session.add(contrato_creado)
                db.session.flush()

                # Vincular contrato al aprendiz si existe
                aprendiz_db = Aprendiz.query.get(current_user.id_aprendiz)
                if aprendiz_db:
                    aprendiz_db.contrato_id = contrato_creado.id_contrato
                    db.session.add(aprendiz_db)

            db.session.commit()
            flash('Empresa y contrato registrados con éxito ✅', 'success')
            return redirect(url_for('empresa_bp.listar_empresas', aprendiz_id=current_user.id_aprendiz))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Ocurrió un error al guardar la empresa o el contrato ❌ {e}', 'danger')

    return render_template('empresa/nueva_empresa.html')


# --- EDITAR EMPRESA ---
@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    contrato = empresa.contratos[0] if empresa.contratos else None

    # Validar permisos: solo el aprendiz dueño puede editar
    if not (hasattr(current_user, 'id_aprendiz') and current_user.id_aprendiz == empresa.aprendiz_id_aprendiz):
        flash('No tienes permisos para editar esta empresa ❌', 'danger')
        return redirect(url_for('empresa_bp.listar_empresas', aprendiz_id=empresa.aprendiz_id_aprendiz))

    if request.method == 'POST':
        try:
            empresa.nombre_empresa = request.form.get('nombre_empresa')
            empresa.nit = request.form.get('nit')
            empresa.direccion = request.form.get('direccion')
            empresa.telefono = request.form.get('telefono')
            empresa.correo_empresa = request.form.get('correo_empresa')
            empresa.nombre_jefe = request.form.get('nombre_jefe')
            empresa.correo_jefe = request.form.get('correo_jefe')
            empresa.telefono_jefe = request.form.get('telefono_jefe')

            # Manejo de contrato: si se envía fecha_inicio, actualizamos (o creamos) contrato
            fecha_inicio_raw = request.form.get('fecha_inicio')
            fecha_fin_raw = request.form.get('fecha_fin')

            if fecha_inicio_raw:
                try:
                    fecha_inicio = datetime.strptime(fecha_inicio_raw, '%Y-%m-%d').date()
                except ValueError:
                    db.session.rollback()
                    flash('Formato de fecha de inicio inválido. Usa YYYY-MM-DD.', 'danger')
                    return redirect(url_for('empresa_bp.editar_empresa', id=id))

                if fecha_fin_raw:
                    try:
                        fecha_fin = datetime.strptime(fecha_fin_raw, '%Y-%m-%d').date()
                    except ValueError:
                        db.session.rollback()
                        flash('Formato de fecha de fin inválido. Usa YYYY-MM-DD.', 'danger')
                        return redirect(url_for('empresa_bp.editar_empresa', id=id))
                else:
                    fecha_fin = add_months(fecha_inicio, 6)

                if contrato:
                    contrato.fecha_inicio = fecha_inicio
                    contrato.fecha_fin = fecha_fin
                    contrato.tipo_contrato = request.form.get('tipo_contrato')
                else:
                    # crear nuevo contrato si antes no existía
                    nuevo_contrato = Contrato(
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        tipo_contrato=request.form.get('tipo_contrato'),
                        empresa_id_empresa=empresa.id_empresa
                    )
                    db.session.add(nuevo_contrato)

            # Si no se envía fecha_inicio, no tocamos el contrato (se mantiene igual)
            if contrato and request.form.get('tipo_contrato') is not None:
                contrato.tipo_contrato = request.form.get('tipo_contrato')

            db.session.commit()
            flash('Empresa y contrato actualizados correctamente ✏️', 'success')
            return redirect(url_for('empresa_bp.listar_empresas', aprendiz_id=empresa.aprendiz_id_aprendiz))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Ocurrió un error al actualizar la empresa o contrato ❌ {e}', 'danger')

    return render_template('empresa/editar_empresa.html', empresa=empresa, contrato=contrato)


# --- ELIMINAR EMPRESA ---
@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_empresa(id):
    empresa = Empresa.query.get_or_404(id)

    # Validar permisos: solo el aprendiz dueño puede eliminar
    if not (hasattr(current_user, 'id_aprendiz') and current_user.id_aprendiz == empresa.aprendiz_id_aprendiz):
        flash('No tienes permisos para eliminar esta empresa ❌', 'danger')
        return redirect(url_for('empresa_bp.listar_empresas', aprendiz_id=empresa.aprendiz_id_aprendiz))

    try:
        db.session.delete(empresa)
        db.session.commit()
        flash('Empresa eliminada con éxito 🗑️', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Ocurrió un error al eliminar la empresa ❌ {e}', 'danger')

    return redirect(url_for('empresa_bp.listar_empresas', aprendiz_id=empresa.aprendiz_id_aprendiz))
