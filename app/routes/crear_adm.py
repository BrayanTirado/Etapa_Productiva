# app/routes/crear_adm.py
import sys
from getpass import getpass
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.users import Administrador

TIPOS_DOCUMENTO = [
    'Cedula de Ciudadania',
    'Tarjeta de Identidad',
    'Cedula Extrangeria',
    'Registro Civil'
]

def crear_administrador():
    print("\n==============================")
    print(" CREACIÓN ADMINISTRADOR PRINCIPAL ")
    print("==============================\n")

    nombre = input("Nombre: ").strip()
    apellido = input("Apellido: ").strip()

    # Selección de tipo de documento guiada
    print("\nTipos de documento:")
    for i, t in enumerate(TIPOS_DOCUMENTO, 1):
        print(f"{i}. {t}")

    while True:
        tipo_index = input("Selecciona el tipo de documento (1-4): ").strip()
        if tipo_index.isdigit() and 1 <= int(tipo_index) <= len(TIPOS_DOCUMENTO):
            tipo_documento = TIPOS_DOCUMENTO[int(tipo_index)-1]
            break
        print("❌ Opción inválida. Intenta de nuevo.")

    documento = input("Número de documento: ").strip()
    correo = input("Correo electrónico: ").strip()
    celular = input("Celular: ").strip()

    # Pedir contraseña de manera segura
    while True:
        password = getpass("Contraseña: ")
        confirmar = getpass("Confirmar contraseña: ")
        if password != confirmar:
            print("❌ Las contraseñas no coinciden. Intenta de nuevo.")
        elif not password:
            print("❌ La contraseña no puede estar vacía.")
        else:
            break

    # Validación de campos
    if not all([nombre, apellido, tipo_documento, documento, correo, celular, password]):
        print("\n❌ Todos los campos son obligatorios.")
        sys.exit(1)

    # Verificar si ya existe un administrador con el mismo correo o documento
    existente = Administrador.query.filter(
        (Administrador.correo == correo) | (Administrador.documento == documento)
    ).first()
    if existente:
        print("\n❌ Ya existe un administrador con ese correo o documento.")
        sys.exit(1)

    hashed_password = generate_password_hash(password)

    admin = Administrador(
        nombre=nombre,
        apellido=apellido,
        tipo_documento=tipo_documento,
        documento=documento,
        correo=correo,
        celular=celular,
        password=hashed_password
    )

    try:
        db.session.add(admin)
        db.session.commit()
        print("\n✅ Administrador creado correctamente.")
    except Exception as e:
        db.session.rollback()
        print("\n❌ Error al crear el administrador:")
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        crear_administrador()
