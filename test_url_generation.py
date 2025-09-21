#!/usr/bin/env python3
"""
Script para probar la generación de URLs en diferentes contextos
"""

import os
from dotenv import load_dotenv
from flask import Flask, url_for
from app import create_app

def test_url_generation():
    """Prueba generación de URLs con y sin SERVER_NAME"""

    print("=" * 60)
    print("PRUEBA DE GENERACIÓN DE URLs")
    print("=" * 60)

    # Cargar variables de entorno
    load_dotenv()

    print(f"SERVER_NAME: {os.environ.get('SERVER_NAME')}")
    print(f"PREFERRED_URL_SCHEME: {os.environ.get('PREFERRED_URL_SCHEME')}")

    # Crear aplicación
    app = create_app()

    with app.app_context():
        print("\nCon contexto de aplicación Flask:")

        # Probar URL sin _external
        try:
            internal_url = url_for('auth.reset_password', token='test-token-123')
            print(f"URL interna: {internal_url}")
        except Exception as e:
            print(f"Error generando URL interna: {e}")

        # Probar URL con _external
        try:
            external_url = url_for('auth.reset_password', token='test-token-123', _external=True)
            print(f"URL externa: {external_url}")
        except Exception as e:
            print(f"Error generando URL externa: {e}")

    print("\n" + "=" * 60)

    # Probar sin contexto de aplicación (simulando producción mal configurada)
    print("Sin contexto de aplicación:")

    # Crear nueva app sin contexto
    app2 = Flask(__name__)
    app2.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
    app2.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

    try:
        with app2.app_context():
            external_url2 = url_for('auth.reset_password', token='test-token-123', _external=True)
            print(f"URL externa (app simple): {external_url2}")
    except Exception as e:
        print(f"Error generando URL externa (app simple): {e}")

if __name__ == "__main__":
    test_url_generation()