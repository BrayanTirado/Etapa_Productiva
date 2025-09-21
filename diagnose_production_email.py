#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de envío de email en producción
Ejecutar en el servidor de producción para identificar la causa del problema
"""

import os
import sys
import smtplib
import socket
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_diagnosis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_environment():
    """Carga las variables de entorno"""
    print("=" * 60)
    print("CARGANDO VARIABLES DE ENTORNO")
    print("=" * 60)

    # Cargar .env si existe
    if os.path.exists('.env'):
        load_dotenv()
        print("[OK] Archivo .env encontrado y cargado")
    else:
        print("[WARNING] Archivo .env no encontrado")

    # Verificar variables críticas
    required_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
    missing_vars = []

    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"[OK] {var}: {'***' if 'PASSWORD' in var else value}")
        else:
            print(f"[ERROR] {var}: NO CONFIGURADO")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n[CRITICAL] Variables faltantes: {', '.join(missing_vars)}")
        return False

    print("[OK] Todas las variables requeridas están configuradas")
    return True

def test_internet_connectivity():
    """Prueba la conectividad a internet"""
    print("\n" + "=" * 60)
    print("PRUEBA DE CONECTIVIDAD A INTERNET")
    print("=" * 60)

    try:
        # Probar conexión a Google DNS
        socket.create_connection(("8.8.8.8", 53), timeout=10)
        print("[OK] Conectividad a internet: OK")
        return True
    except Exception as e:
        print(f"[ERROR] Sin conectividad a internet: {e}")
        return False

def test_smtp_port_accessibility(server, port):
    """Verifica si el puerto SMTP es accesible"""
    print(f"\nVerificando acceso al puerto {port} en {server}...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((server, port))
        sock.close()

        if result == 0:
            print(f"[OK] Puerto {port} accesible")
            return True
        else:
            print(f"[ERROR] Puerto {port} bloqueado o inaccesible")
            return False
    except Exception as e:
        print(f"[ERROR] Error verificando puerto {port}: {e}")
        return False

def test_smtp_connection():
    """Prueba la conexión SMTP completa"""
    print("\n" + "=" * 60)
    print("PRUEBA DE CONEXIÓN SMTP")
    print("=" * 60)

    server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    port = int(os.environ.get('MAIL_PORT', 587))
    username = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    use_ssl = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'

    print(f"Servidor: {server}")
    print(f"Puerto: {port}")
    print(f"Usuario: {username}")
    print(f"Usar TLS: {use_tls}")
    print(f"Usar SSL: {use_ssl}")

    # Verificar puerto accesible
    if not test_smtp_port_accessibility(server, port):
        return False

    try:
        print("\nIntentando conectar al servidor SMTP...")

        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=30)
        else:
            smtp = smtplib.SMTP(server, port, timeout=30)

        print("[OK] Conexión inicial exitosa")

        # Habilitar debug para más información
        smtp.set_debuglevel(1)

        if use_tls:
            print("Iniciando TLS...")
            smtp.starttls()
            print("[OK] TLS iniciado correctamente")

        if username and password:
            print("Autenticando...")
            smtp.login(username, password)
            print("[OK] Autenticación exitosa")

        smtp.quit()
        print("[OK] Conexión cerrada correctamente")
        print("[SUCCESS] PRUEBA DE CONEXIÓN SMTP EXITOSA")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERROR] Error de autenticación: {e}")
        print("Solución: Verificar que MAIL_PASSWORD sea una contraseña de aplicación de Gmail")
        print("Crear contraseña de aplicación en: https://myaccount.google.com/apppasswords")
    except smtplib.SMTPConnectError as e:
        print(f"[ERROR] Error de conexión: {e}")
        print("Solución: Verificar conectividad a internet y configuración del firewall")
    except smtplib.SMTPException as e:
        print(f"[ERROR] Error SMTP: {e}")
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

    print("[FAILED] PRUEBA DE CONEXIÓN SMTP FALLIDA")
    return False

def test_email_sending():
    """Prueba el envío real de un email"""
    print("\n" + "=" * 60)
    print("PRUEBA DE ENVÍO DE EMAIL")
    print("=" * 60)

    server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    port = int(os.environ.get('MAIL_PORT', 587))
    username = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    sender = os.environ.get('MAIL_DEFAULT_SENDER', username)
    use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    use_ssl = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'

    # Email de prueba (enviar a sí mismo)
    test_recipient = sender
    test_subject = "Prueba de Email - Diagnóstico de Producción"
    test_body = """
    Este es un email de prueba enviado desde el script de diagnóstico.

    Si recibes este email, significa que:
    - La configuración SMTP es correcta
    - Las credenciales son válidas
    - El servidor puede enviar emails

    Fecha de envío: {datetime}
    Servidor: {server}:{port}
    Usuario: {username}
    """.format(
        datetime=os.popen('date /t').read().strip() if os.name == 'nt' else os.popen('date').read().strip(),
        server=server,
        port=port,
        username=username
    )

    try:
        print(f"Enviando email de prueba a: {test_recipient}")

        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=30)
        else:
            smtp = smtplib.SMTP(server, port, timeout=30)

        smtp.set_debuglevel(1)

        if use_tls:
            smtp.starttls()

        smtp.login(username, password)

        # Crear mensaje con codificación UTF-8
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = test_recipient
        message['Subject'] = test_subject

        # Adjuntar el cuerpo como texto plano con codificación UTF-8
        message.attach(MIMEText(test_body, 'plain', 'utf-8'))

        smtp.sendmail(sender, test_recipient, message.as_string())
        smtp.quit()

        print("[SUCCESS] Email de prueba enviado exitosamente")
        print(f"[INFO] Revisa la bandeja de entrada de {test_recipient}")
        return True

    except Exception as e:
        print(f"[ERROR] Error enviando email de prueba: {e}")
        return False

def check_gmail_security():
    """Verifica configuraciones de seguridad de Gmail"""
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE SEGURIDAD GMAIL")
    print("=" * 60)

    username = os.environ.get('MAIL_USERNAME', '')

    if not username.endswith('@gmail.com'):
        print("[INFO] No es una cuenta Gmail, omitiendo verificación específica")
        return

    print("[GMAIL] Recordatorios importantes:")
    print("1. Verificar que la autenticación de 2 factores esté ACTIVADA")
    print("2. MAIL_PASSWORD debe ser una 'contraseña de aplicación', no la contraseña normal")
    print("3. Crear contraseña de aplicación en: https://myaccount.google.com/apppasswords")
    print("4. Verificar que no haya restricciones de seguridad activas")
    print("5. Revisar si Gmail está bloqueando el acceso desde 'aplicaciones menos seguras'")
    print("6. Verificar el historial de actividad reciente en la cuenta Gmail")

def main():
    """Función principal del diagnóstico"""
    print("SCRIPT DE DIAGNÓSTICO DE EMAIL EN PRODUCCIÓN")
    print("Ejecutado en:", os.popen('date').read().strip())
    print("Servidor:", os.popen('hostname').read().strip())

    # Paso 1: Cargar entorno
    if not load_environment():
        print("\n[CRITICAL] Variables de entorno no configuradas correctamente")
        sys.exit(1)

    # Paso 2: Conectividad a internet
    if not test_internet_connectivity():
        print("\n[CRITICAL] Sin conectividad a internet")
        sys.exit(1)

    # Paso 3: Conexión SMTP
    if not test_smtp_connection():
        print("\n[CRITICAL] Conexión SMTP fallida")
        sys.exit(1)

    # Paso 4: Envío de email de prueba
    if not test_email_sending():
        print("\n[CRITICAL] Envío de email fallido")
        sys.exit(1)

    # Paso 5: Verificaciones específicas de Gmail
    check_gmail_security()

    print("\n" + "=" * 60)
    print("DIAGNÓSTICO COMPLETADO EXITOSAMENTE")
    print("=" * 60)
    print("[SUCCESS] Todas las pruebas pasaron correctamente")
    print("[INFO] Si el problema persiste, revisar:")
    print("1. Logs del servidor web (Nginx/Apache)")
    print("2. Configuración del firewall")
    print("3. Restricciones del proveedor de hosting")
    print("4. Configuración DNS y SPF")

if __name__ == "__main__":
    main()