# app/routes/sedes_route.py
from flask import Blueprint
from app import db
from app.models.users import Sede

sedes_bp = Blueprint('sedes_bp', __name__, url_prefix='/sedes')

def insertar_sedes():
    # Diccionario de siglas -> ciudades (puedes cambiar las ciudades según corresponda)
    ciudades = {
        'CGAO': 'Bogotá',
        'CCS': 'Medellín',
        'CDM': 'Cali',
        'CGAF': 'Bucaramanga',
        'CGPI': 'Barranquilla',
        'CTIC': 'Cartagena',
        'CBA': 'Pasto',
        'CEM': 'Manizales',
        'CSF': 'Santa Marta',
        'CFGR': 'Ibagué'
    }

    creadas = 0
    for sigla, ciudad in ciudades.items():
        # Solo insertar si no existe la sede
        if not Sede.query.filter_by(nombre_sede=sigla).first():
            nueva_sede = Sede(nombre_sede=sigla, ciudad=ciudad)
            db.session.add(nueva_sede)
            creadas += 1

    if creadas > 0:
        db.session.commit()
        print(f"[INFO] {creadas} sedes fueron registradas automáticamente.")
    else:
         print("[INFO] Todas las sedes ya estaban registradas.")
