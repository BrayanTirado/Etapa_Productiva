#!/usr/bin/env python3
"""
Script de diagnóstico específico para problemas de email en producción
Ejecuta este script en tu servidor de producción para identificar el problema exacto
"""

import os
import sys
from dotenv import load_dotenv

def diagnose_production_email():
    """Diagnóstico completo de problemas de email en producción"""

    print("=" * 80)
    print("DIAGNÓSTICO DE EMAIL EN PRODUCCIÓN")
    print("=" * 80)

    # 1. Verificar entorno
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")

    # 2. Verificar archivo .env
    env_path = os.path.join(os.getcwd(), '.env')
    print(f"\nArchivo .env existe: {os.path.exists(env_path)}")
    if os.path.exists(env_path):
        print(f"Ruta: {env_path}")
        print(f"Tamaño: {os.path.getsize(env_path)} bytes")
        print(f"Permisos: {oct(os.stat(env_path).st_mode)[-3:]}")

        # Mostrar contenido (sin contraseñas)
        print("\nContenido del .env:")
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if 'PASSWORD' in line.upper():
                            key = line.split('=')[0]
                            print(f"  {i:2d}. {key}=***OCULTO***")
                        else:
                            print(f"  {i:2d}. {line}")
        except Exception as e:
            print(f"  Error leyendo .env: {e}")
    else:
        print("❌ CRÍTICO: Archivo .env NO encontrado")
        print("   Solución: Copia el .env desde desarrollo al servidor")

    # 3. Cargar variables de entorno
    print("
🔄 Cargando variables de entorno..."    load_dotenv()
    print("✓ load_dotenv() ejecutado"

    # 4. Verificar variables críticas
    print("
📋 Variables de entorno críticas:"    critical_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
    all_present = True

    for var in critical_vars:
        value = os.environ.get(var)
        status = "✓ Presente" if value else "✗ Ausente"
        if value and 'PASSWORD' not in var.upper():
            print(f"  {var}: {status} ({value})")
        else:
            print(f"  {var}: {status}")
        if not value:
            all_present = False

    # 5. Verificar otras variables importantes
    print("
🔧 Otras variables importantes:"    other_vars = ['SERVER_NAME', 'PREFERRED_URL_SCHEME', 'PROXY_FIX_ENABLED']
    for var in other_vars:
        value = os.environ.get(var, 'No definido')
        print(f"  {var}: {value}")

    # 6. Probar conectividad básica
    print("
🌐 Probando conectividad:"    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        print("  ✓ Conectividad a internet: OK")
    except Exception as e:
        print(f"  ✗ Conectividad a internet: FALLANDO - {e}")
        print("    Esto impedirá completamente el envío de emails")

    # 7. Probar puerto SMTP
    print("
📮 Probando puerto SMTP (587):"    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('smtp.gmail.com', 587))
        sock.close()
        if result == 0:
            print("  ✓ Puerto 587 accesible")
        else:
            print("  ✗ Puerto 587 bloqueado o inaccesible")
            print("    El firewall puede estar bloqueando SMTP")
    except Exception as e:
        print(f"  ✗ Error probando puerto 587: {e}")

    # 8. Probar autenticación SMTP
    print("
🔐 Probando autenticación SMTP:"    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')

    if mail_username and mail_password:
        try:
            import smtplib
            print("  Conectando a smtp.gmail.com:587...")
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.set_debuglevel(0)  # Sin debug para no saturar logs

            print("  Iniciando TLS...")
            server.starttls()

            print("  Autenticando...")
            server.login(mail_username, mail_password)

            print("  ✓ Autenticación SMTP exitosa")
            server.quit()

        except smtplib.SMTPAuthenticationError as e:
            print(f"  ✗ Error de autenticación: {e}")
            print("    Verifica que MAIL_USERNAME y MAIL_PASSWORD sean correctos")
            print("    Para Gmail: Usa contraseña de aplicación, no la contraseña normal")
        except smtplib.SMTPConnectError as e:
            print(f"  ✗ Error de conexión: {e}")
            print("    Verifica conectividad a internet")
        except Exception as e:
            print(f"  ✗ Error inesperado: {e}")
    else:
        print("  ✗ No se puede probar autenticación: credenciales faltantes")

    # 9. Simular envío de email
    print("
📧 Probando envío de email:"    if all_present and mail_username and mail_password:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Crear mensaje de prueba
            message = MIMEMultipart()
            message['From'] = mail_username
            message['To'] = mail_username  # Enviar a sí mismo
            message['Subject'] = 'Prueba de email - Diagnóstico producción'

            body = """
Este es un email de prueba enviado desde el diagnóstico de producción.

Si recibes este email, significa que:
- La configuración SMTP es correcta
- Las credenciales son válidas
- El servidor puede enviar emails

Si no lo recibes, el problema está en:
- Configuración del servidor
- Firewall bloqueando SMTP
- Credenciales incorrectas
- Problemas de red
            """.strip()

            message.attach(MIMEText(body, 'plain'))

            print("  Enviando email de prueba...")
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_username, mail_username, message.as_string())
            server.quit()

            print("  ✓ Email de prueba enviado exitosamente")
            print(f"  ✓ Revisa la bandeja de entrada de {mail_username}")

        except Exception as e:
            print(f"  ✗ Error enviando email de prueba: {e}")
    else:
        print("  ✗ No se puede enviar email de prueba: configuración incompleta")

    # 10. Resumen y recomendaciones
    print("
" + "=" * 80)
    print("RESUMEN Y RECOMENDACIONES")
    print("=" * 80)

    issues = []

    if not os.path.exists(env_path):
        issues.append("Archivo .env faltante")
    if not all_present:
        issues.append("Variables de entorno faltantes")
    if not mail_username or not mail_password:
        issues.append("Credenciales SMTP faltantes")

    if issues:
        print("❌ PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"   • {issue}")

        print("
💡 RECOMENDACIONES:"        print("   1. Copia el archivo .env completo desde desarrollo")
        print("   2. Verifica que todas las variables estén definidas")
        print("   3. Para Gmail, usa contraseña de aplicación")
        print("   4. Verifica que el servidor tenga acceso a internet")
        print("   5. Verifica que el puerto 587 no esté bloqueado por firewall")
    else:
        print("✅ CONFIGURACIÓN BÁSICA CORRECTA")
        print("
💡 SI AÚN HAY PROBLEMAS:"        print("   • Verifica que la aplicación Flask se inicie correctamente")
        print("   • Revisa los logs de la aplicación en producción")
        print("   • Verifica que Flask-Mail esté inicializado")
        print("   • Considera problemas de contexto de aplicación")

    print("
📝 COMANDO PARA EJECUTAR EN PRODUCCIÓN:"    print("   python diagnose_production_email.py")
    print("=" * 80)

if __name__ == "__main__":
    diagnose_production_email()