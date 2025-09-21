#!/usr/bin/env python3
"""
Script de diagnóstico para verificar configuración de email en producción
Ejecutar en el servidor de producción para identificar problemas
"""

import os
import sys
import smtplib
import socket

def check_environment_variables():
    """Verifica las variables de entorno necesarias"""
    print("=" * 60)
    print("VERIFICACIÓN DE VARIABLES DE ENTORNO")
    print("=" * 60)

    required_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
    all_present = True

    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if 'PASSWORD' in var:
                print(f"[OK] {var}: *** (configurado)")
            else:
                print(f"[OK] {var}: {value}")
        else:
            print(f"[ERROR] {var}: NO CONFIGURADO")
            all_present = False

    return all_present

def check_smtp_connection():
    """Verifica la conexión SMTP"""
    print("\n" + "=" * 60)
    print("PRUEBA DE CONEXIÓN SMTP")
    print("=" * 60)

    # Configuración
    server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    port = int(os.environ.get('MAIL_PORT', 465))
    username = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    use_ssl = os.environ.get('MAIL_USE_SSL', 'true').lower() == 'true'
    use_tls = os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true'

    print(f"Servidor: {server}")
    print(f"Puerto: {port}")
    print(f"Usuario: {username}")
    print(f"SSL: {use_ssl}")
    print(f"TLS: {use_tls}")

    # Verificar puerto accesible
    print(f"\nVerificando acceso al puerto {port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((server, port))
        sock.close()

        if result == 0:
            print(f"[OK] Puerto {port} accesible")
        else:
            print(f"[ERROR] Puerto {port} BLOQUEADO o inaccesible")
            print("   Esto impide el envío de emails")
            return False
    except Exception as e:
        print(f"[ERROR] Error verificando puerto {port}: {e}")
        return False

    # Probar conexión SMTP
    print("\nProbando conexión SMTP completa...")
    try:
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=30)
        else:
            smtp = smtplib.SMTP(server, port, timeout=30)

        smtp.set_debuglevel(1)  # Debug output

        if use_tls and not use_ssl:
            smtp.starttls()

        if username and password:
            smtp.login(username, password)
            print("[OK] Autenticación exitosa")

        smtp.quit()
        print("[OK] Conexión SMTP exitosa")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERROR] Error de autenticación: {e}")
        print("   Verificar MAIL_USERNAME y MAIL_PASSWORD")
        return False
    except Exception as e:
        print(f"[ERROR] Error de conexión SMTP: {e}")
        return False

def test_email_sending():
    """Prueba el envío real de un email"""
    print("\n" + "=" * 60)
    print("PRUEBA DE ENVÍO DE EMAIL")
    print("=" * 60)

    # Simular la función send_reset_email
    try:
        from flask import Flask
        from flask_mail import Mail, Message

        # Crear app mínima para testing
        app = Flask(__name__)
        app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 465))
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
        app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
        app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'true').lower() == 'true'
        app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true'

        mail = Mail(app)

        with app.app_context():
            # Email de prueba (enviar a sí mismo)
            test_email = os.environ.get('MAIL_DEFAULT_SENDER', 'test@example.com')
            test_url = 'https://ejemplo.com/reset/test-token'

            msg = Message(
                subject='Prueba de Email - Diagnóstico',
                recipients=[test_email],
                sender=app.config['MAIL_DEFAULT_SENDER'],
                body=f'Prueba de email desde servidor de producción\n\nURL: {test_url}'
            )

            print(f"Enviando email de prueba a: {test_email}")
            mail.send(msg)
            print("[SUCCESS] Email enviado exitosamente")
            return True

    except Exception as e:
        print(f"[ERROR] Error enviando email: {e}")
        return False

def main():
    """Función principal"""
    print("DIAGNÓSTICO DE EMAIL EN PRODUCCIÓN")
    print("Ejecutado en:", os.popen('hostname').read().strip() if os.name != 'nt' else 'Windows')

    # Paso 1: Variables de entorno
    env_ok = check_environment_variables()

    if not env_ok:
        print("\n[CRITICAL] ERROR CRÍTICO: Variables de entorno no configuradas")
        print("Configurar en el servidor de producción:")
        print("export MAIL_USERNAME=tu-email@gmail.com")
        print("export MAIL_PASSWORD=tu-contraseña-aplicación")
        print("export MAIL_DEFAULT_SENDER=tu-email@gmail.com")
        return

    # Paso 2: Conexión SMTP
    smtp_ok = check_smtp_connection()

    if not smtp_ok:
        print("\n[CRITICAL] ERROR: Conexión SMTP fallida")
        print("Posibles soluciones:")
        print("1. Verificar que el puerto 465 no esté bloqueado por firewall")
        print("2. Intentar con puerto 587 (TLS) en lugar de 465 (SSL)")
        print("3. Contactar al proveedor de hosting para permitir SMTP")
        return

    # Paso 3: Prueba de envío
    email_ok = test_email_sending()

    # Resultado final
    print("\n" + "=" * 60)
    if email_ok:
        print("[SUCCESS] DIAGNÓSTICO EXITOSO: Los emails deberían funcionar")
    else:
        print("[FAILED] DIAGNÓSTICO FALLIDO: Revisar logs para más detalles")

if __name__ == "__main__":
    main()