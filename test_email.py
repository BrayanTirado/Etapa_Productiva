#!/usr/bin/env python3
"""
Script de prueba para diagnosticar problemas de envío de emails
Ejecuta este script para verificar la configuración de email
"""

import os
import sys
import smtplib
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_smtp_connection():
    """Prueba la conexión SMTP"""
    print("=" * 60)
    print("PRUEBA DE CONEXIÓN SMTP - DIAGNÓSTICO")
    print("=" * 60)

    # Obtener configuración
    server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    port = int(os.environ.get('MAIL_PORT', '587'))
    username = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    use_tls = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    use_ssl = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'

    print("Configuración actual:")
    print(f"  Servidor: {server}")
    print(f"  Puerto: {port}")
    print(f"  Usuario: {username}")
    print(f"  Contraseña: {'***configurada***' if password else 'NO CONFIGURADA'}")
    print(f"  Usar TLS: {use_tls}")
    print(f"  Usar SSL: {use_ssl}")
    print()

    # Verificar configuración básica
    if not username or not password:
        print("❌ ERROR: MAIL_USERNAME o MAIL_PASSWORD no están configurados")
        print("   Revisa tu archivo .env")
        return False

    try:
        print("🔄 Intentando conectar al servidor SMTP...")

        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
            print("✅ Conexión SSL establecida")
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
            print("✅ Conexión SMTP establecida")

        if use_tls:
            smtp.starttls()
            print("✅ TLS iniciado correctamente")

        print("🔄 Intentando autenticación...")
        smtp.login(username, password)
        print("✅ Autenticación exitosa")

        smtp.quit()
        print("✅ Conexión cerrada correctamente")

        print("\n✅ PRUEBA DE CONEXIÓN SMTP EXITOSA")
        print("   El problema podría estar en la configuración de Flask-Mail")
        print("   o en la generación de URLs externas.")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ ERROR DE AUTENTICACIÓN: {e}")
        print("\nPosibles soluciones:")
        print("  • Para Gmail: Asegúrate de tener activada la autenticación de 2 factores")
        print("  • Para Gmail: Usa una 'contraseña de aplicación', no tu contraseña normal")
        print("  • Crea una contraseña de aplicación en: https://myaccount.google.com/apppasswords")
        print("  • Verifica que no haya restricciones de seguridad en tu cuenta Gmail")

    except smtplib.SMTPConnectError as e:
        print(f"❌ ERROR DE CONEXIÓN: {e}")
        print("\nPosibles soluciones:")
        print(f"  • Verifica que el puerto {port} no esté bloqueado por firewall")
        print("  • Verifica que el servidor tenga acceso a internet")
        print("  • Prueba con un servidor DNS diferente")

    except smtplib.SMTPException as e:
        print(f"❌ ERROR SMTP: {e}")
        print("\nPosibles soluciones:")
        print("  • Verifica la configuración del servidor SMTP")
        print("  • Intenta cambiar el puerto (587 para TLS, 465 para SSL)")

    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

    print("\n❌ PRUEBA DE CONEXIÓN SMTP FALLIDA")
    return False

def test_flask_mail():
    """Prueba Flask-Mail con la configuración actual"""
    print("\n" + "=" * 60)
    print("PRUEBA DE FLASK-MAIL")
    print("=" * 60)

    try:
        from flask import Flask
        from flask_mail import Mail, Message

        app = Flask(__name__)

        # Configurar Flask-Mail
        app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
        app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
        app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
        app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

        mail = Mail(app)

        with app.app_context():
            print("🔄 Intentando enviar email de prueba con Flask-Mail...")

            msg = Message(
                subject='Prueba de Email - Sistema SENA',
                recipients=[app.config['MAIL_DEFAULT_SENDER']],
                body='Este es un email de prueba para verificar la configuración de Flask-Mail.'
            )

            mail.send(msg)
            print("✅ Email enviado exitosamente con Flask-Mail")
            return True

    except Exception as e:
        print(f"❌ ERROR con Flask-Mail: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO DE CONFIGURACIÓN DE EMAIL")
    print("Este script probará la configuración de envío de emails")
    print()

    # Prueba 1: Conexión SMTP básica
    smtp_ok = test_smtp_connection()

    # Prueba 2: Flask-Mail (solo si SMTP funciona)
    if smtp_ok:
        flask_mail_ok = test_flask_mail()
        if flask_mail_ok:
            print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
            print("   El envío de emails debería funcionar correctamente")
        else:
            print("\n⚠️  SMTP funciona pero Flask-Mail tiene problemas")
            print("   El problema podría estar en la configuración de Flask")
    else:
        print("\n❌ Las pruebas básicas fallaron")
        print("   Corrige los problemas de configuración antes de continuar")

    print("\n" + "=" * 60)
    print("FIN DEL DIAGNÓSTICO")
    print("=" * 60)