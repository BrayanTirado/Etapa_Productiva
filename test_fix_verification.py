#!/usr/bin/env python3
"""
Script para verificar que la solución del proxy reverso funciona correctamente
"""

import os
from dotenv import load_dotenv
from app import create_app

def test_fix_verification():
    """Verifica que la solución funcione correctamente"""

    print("=" * 60)
    print("VERIFICACIÓN DE LA SOLUCIÓN DE PROXY")
    print("=" * 60)

    # Cargar variables de entorno
    load_dotenv()

    print(f"SERVER_NAME: {os.environ.get('SERVER_NAME')}")
    print(f"PREFERRED_URL_SCHEME: {os.environ.get('PREFERRED_URL_SCHEME')}")
    print(f"PROXY_FIX_ENABLED: {os.environ.get('PROXY_FIX_ENABLED')}")

    # Crear aplicación con la nueva configuración
    app = create_app()

    with app.app_context():
        print("\nProbando generación de URLs con la aplicación completa:")

        try:
            # Probar URL externa para reset_password
            from flask import url_for
            reset_url = url_for('auth.reset_password', token='test-token-123', _external=True)
            print(f"[OK] URL de reset generada correctamente: {reset_url}")

            # Verificar que la URL tenga el formato correcto
            if 'https://' in reset_url and 'senaproductiva.isladigital.xyz' in reset_url:
                print("[OK] URL tiene el formato HTTPS correcto")
                print("[OK] URL contiene el dominio correcto")
            else:
                print("[ERROR] URL no tiene el formato esperado")
                print(f"   Esperado: https://senaproductiva.isladigital.xyz/...")
                print(f"   Obtenido: {reset_url}")

        except Exception as e:
            print(f"[ERROR] Error generando URL: {e}")
            print("   Esto indica que el problema persiste")

    print("\n" + "=" * 60)
    print("INSTRUCCIONES PARA PRODUCCIÓN:")
    print("1. Despliega los cambios en tu servidor")
    print("2. Reinicia la aplicación")
    print("3. Prueba el envío de email de recuperación de contraseña")
    print("4. Verifica que el email llegue correctamente")
    print("=" * 60)

if __name__ == "__main__":
    test_fix_verification()