#!/usr/bin/env python3
"""
Script para simular el escenario de producción con proxy reverso
"""

import os
from dotenv import load_dotenv
from flask import Flask, url_for, request
from werkzeug.middleware.proxy_fix import ProxyFix

def test_proxy_scenarios():
    """Prueba diferentes escenarios de proxy"""

    print("=" * 60)
    print("PRUEBA DE ESCENARIOS DE PROXY")
    print("=" * 60)

    # Cargar variables de entorno
    load_dotenv()

    print(f"SERVER_NAME: {os.environ.get('SERVER_NAME')}")
    print(f"PREFERRED_URL_SCHEME: {os.environ.get('PREFERRED_URL_SCHEME')}")

    # Escenario 1: Flask normal (como en desarrollo)
    print("\n1. ESCENARIO: Flask normal (desarrollo)")
    app1 = Flask(__name__)
    app1.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
    app1.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

    with app1.app_context():
        try:
            # Simular request normal
            with app1.test_request_context('/'):
                url = url_for('index', _external=True)
                print(f"   URL generada: {url}")
        except Exception as e:
            print(f"   Error: {e}")

    # Escenario 2: Flask detrás de proxy SIN ProxyFix
    print("\n2. ESCENARIO: Flask detrás de proxy SIN ProxyFix")
    app2 = Flask(__name__)
    app2.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
    app2.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

    with app2.app_context():
        try:
            # Simular request con headers de proxy
            with app2.test_request_context(
                '/',
                headers={
                    'X-Forwarded-Proto': 'https',
                    'X-Forwarded-Host': 'senaproductiva.isladigital.xyz',
                    'X-Real-IP': '127.0.0.1'
                }
            ):
                url = url_for('index', _external=True)
                print(f"   URL generada: {url}")
                print(f"   Request URL: {request.url}")
        except Exception as e:
            print(f"   Error: {e}")

    # Escenario 3: Flask detrás de proxy CON ProxyFix
    print("\n3. ESCENARIO: Flask detrás de proxy CON ProxyFix")
    app3 = Flask(__name__)
    app3.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
    app3.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

    # Aplicar ProxyFix middleware
    app3.wsgi_app = ProxyFix(app3.wsgi_app, x_proto=1, x_host=1)

    with app3.app_context():
        try:
            # Simular request con headers de proxy
            with app3.test_request_context(
                '/',
                headers={
                    'X-Forwarded-Proto': 'https',
                    'X-Forwarded-Host': 'senaproductiva.isladigital.xyz',
                    'X-Real-IP': '127.0.0.1'
                }
            ):
                url = url_for('index', _external=True)
                print(f"   URL generada: {url}")
                print(f"   Request URL: {request.url}")
        except Exception as e:
            print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("CONCLUSIÓN:")
    print("Si en producción Flask está detrás de un proxy reverso,")
    print("necesitas configurar ProxyFix para que las URLs externas")
    print("se generen correctamente.")
    print("=" * 60)

if __name__ == "__main__":
    test_proxy_scenarios()