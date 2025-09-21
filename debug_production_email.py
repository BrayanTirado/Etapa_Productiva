#!/usr/bin/env python3
"""
Script para debug detallado del envío de emails en producción
"""

import os
import sys
from dotenv import load_dotenv
from flask import Flask, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

def simulate_production_context():
    """Simula el contexto de producción para identificar el problema"""

    print("=" * 70)
    print("DEBUG DETALLADO DE ENVÍO DE EMAIL - CONTEXTO PRODUCCIÓN")
    print("=" * 70)

    # Cargar variables de entorno
    load_dotenv()

    print(f"SERVER_NAME: {os.environ.get('SERVER_NAME')}")
    print(f"PREFERRED_URL_SCHEME: {os.environ.get('PREFERRED_URL_SCHEME')}")
    print(f"PROXY_FIX_ENABLED: {os.environ.get('PROXY_FIX_ENABLED')}")

    # Crear aplicación Flask como en producción
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
    app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')

    # Configuración de email
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    # Aplicar ProxyFix como en producción
    if os.environ.get('PROXY_FIX_ENABLED', 'true').lower() == 'true':
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
        )
        print("[PROXY] ProxyFix aplicado")

    # Inicializar Flask-Mail
    from flask_mail import Mail
    mail = Mail(app)

    # Simular headers de proxy reverso (como en producción)
    proxy_headers = {
        'X-Forwarded-Proto': 'https',
        'X-Forwarded-Host': 'senaproductiva.isladigital.xyz',
        'X-Real-IP': '127.0.0.1'
    }

    with app.app_context():
        print("\n[TEST] Probando generación de URL...")
        try:
            # Simular request con headers de proxy
            with app.test_request_context('/', headers=proxy_headers):
                test_token = 'test-token-123'
                # Usar URL absoluta directamente en lugar de url_for
                reset_url = f"{app.config['PREFERRED_URL_SCHEME']}://{app.config['SERVER_NAME']}/auth/reset_password/{test_token}"
                print(f"[OK] URL generada: {reset_url}")
        except Exception as e:
            print(f"[ERROR] Error generando URL: {e}")
            return False

        print("\n[TEST] Probando envío de email...")

        # Simular la función send_reset_email
        email = 'test@example.com'
        reset_url = 'https://senaproductiva.isladigital.xyz/auth/reset_password/test-token-123'

        try:
            from flask_mail import Message

            msg = Message(
                subject='Recuperación de contraseña - SENA',
                recipients=[email],
                sender=app.config['MAIL_DEFAULT_SENDER'],
                body=f"""
Hola,

Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para continuar:

{reset_url}

Este enlace expirará en 1 hora.

Si no solicitaste este cambio, ignora este mensaje.

Atentamente,
Sistema SENA
                """.strip()
            )

            print("[EMAIL] Mensaje creado correctamente")
            print(f"[EMAIL] Destinatario: {email}")
            print(f"[EMAIL] Remitente: {app.config['MAIL_DEFAULT_SENDER']}")
            print(f"[EMAIL] Servidor: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")

            # Intentar enviar
            print("[EMAIL] Intentando enviar email...")
            mail.send(msg)

            print("[SUCCESS] Email enviado exitosamente")
            return True

        except Exception as e:
            print(f"[ERROR] Error al enviar email: {e}")
            print(f"[ERROR] Tipo de error: {type(e).__name__}")

            # Diagnosticar el error
            if "SMTP" in str(e):
                print("[DIAG] Parece ser un problema de conexión SMTP")
                print("       Verifica que el servidor tenga acceso a internet")
                print("       Verifica que el puerto 587 no esté bloqueado")
            elif "authentication" in str(e).lower():
                print("[DIAG] Problema de autenticación")
                print("       Verifica que MAIL_USERNAME y MAIL_PASSWORD sean correctos")
                print("       Para Gmail, asegúrate de usar una contraseña de aplicación")
            elif "connection" in str(e).lower():
                print("[DIAG] Problema de conexión")
                print("       Verifica la conectividad a internet del servidor")

            import traceback
            print(f"[TRACEBACK] {traceback.format_exc()}")
            return False

def simulate_development_context():
    """Simula el contexto de desarrollo para comparar"""

    print("\n" + "=" * 70)
    print("DEBUG DETALLADO DE ENVÍO DE EMAIL - CONTEXTO DESARROLLO")
    print("=" * 70)

    # Cargar variables de entorno
    load_dotenv()

    # Crear aplicación Flask como en desarrollo
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['SERVER_NAME'] = None  # En desarrollo no hay SERVER_NAME
    app.config['PREFERRED_URL_SCHEME'] = 'http'  # En desarrollo es HTTP

    # Configuración de email
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    # NO aplicar ProxyFix en desarrollo
    print("[DEV] Sin ProxyFix (modo desarrollo)")

    # Inicializar Flask-Mail
    from flask_mail import Mail
    mail = Mail(app)

    with app.app_context():
        print("\n[TEST] Probando generación de URL...")
        try:
            # Simular request normal de desarrollo
            with app.test_request_context('/'):
                test_token = 'test-token-123'
                reset_url = f'http://localhost:8080/auth/reset_password/{test_token}'
                print(f"[OK] URL generada: {reset_url}")
        except Exception as e:
            print(f"[ERROR] Error generando URL: {e}")
            return False

        print("\n[TEST] Probando envío de email...")

        # Simular la función send_reset_email
        email = 'test@example.com'
        reset_url = 'http://localhost:8080/auth/reset_password/test-token-123'

        try:
            from flask_mail import Message

            msg = Message(
                subject='Recuperación de contraseña - SENA',
                recipients=[email],
                sender=app.config['MAIL_DEFAULT_SENDER'],
                body=f"""
Hola,

Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para continuar:

{reset_url}

Este enlace expirará en 1 hora.

Si no solicitaste este cambio, ignora este mensaje.

Atentamente,
Sistema SENA
                """.strip()
            )

            print("[EMAIL] Mensaje creado correctamente")
            print(f"[EMAIL] Destinatario: {email}")
            print(f"[EMAIL] Remitente: {app.config['MAIL_DEFAULT_SENDER']}")
            print(f"[EMAIL] Servidor: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")

            # Intentar enviar
            print("[EMAIL] Intentando enviar email...")
            mail.send(msg)

            print("[SUCCESS] Email enviado exitosamente")
            return True

        except Exception as e:
            print(f"[ERROR] Error al enviar email: {e}")
            print(f"[ERROR] Tipo de error: {type(e).__name__}")

            import traceback
            print(f"[TRACEBACK] {traceback.format_exc()}")
            return False

if __name__ == "__main__":
    print("Comparando contextos de desarrollo vs producción...\n")

    # Probar desarrollo primero
    dev_success = simulate_development_context()

    # Probar producción
    prod_success = simulate_production_context()

    print("\n" + "=" * 70)
    print("RESUMEN DE RESULTADOS")
    print("=" * 70)
    print(f"Desarrollo: {'[OK] EXITOSO' if dev_success else '[ERROR] FALLO'}")
    print(f"Producción: {'[OK] EXITOSO' if prod_success else '[ERROR] FALLO'}")

    if dev_success and not prod_success:
        print("\n🔍 DIAGNÓSTICO:")
        print("   El problema está específicamente en el contexto de producción.")
        print("   Posibles causas:")
        print("   • Variables de entorno no disponibles en el servidor")
        print("   • Problemas de conectividad en el servidor de producción")
        print("   • Configuración de ProxyFix causando problemas")
        print("   • Flask-Mail no inicializado correctamente en producción")
    elif not dev_success and not prod_success:
        print("\n🔍 DIAGNÓSTICO:")
        print("   El problema es general, no específico de producción.")
        print("   Verificar configuración de Gmail y conectividad.")
    else:
        print("\n✅ Ambos contextos funcionan correctamente.")