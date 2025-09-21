#!/usr/bin/env python3
"""
Script de diagnóstico para verificar configuración de email en producción
Ejecuta este script en tu servidor de producción para identificar el problema
"""

import os
import sys
from dotenv import load_dotenv

def diagnose_email_config():
    """Diagnóstico completo de la configuración de email"""
    print("=" * 60)
    print("DIAGNÓSTICO DE CONFIGURACIÓN DE EMAIL - PRODUCCIÓN")
    print("=" * 60)

    # 1. Verificar directorio de trabajo
    print(f"Directorio actual: {os.getcwd()}")
    print(f"Directorio del script: {os.path.dirname(os.path.abspath(__file__))}")

    # 2. Verificar si existe el archivo .env
    env_path = os.path.join(os.getcwd(), '.env')
    print(f"\nArchivo .env existe: {os.path.exists(env_path)}")
    if os.path.exists(env_path):
        print(f"Ruta completa: {env_path}")
        print(f"Tamaño del archivo: {os.path.getsize(env_path)} bytes")

        # Mostrar contenido del .env (sin contraseñas)
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
            print(f"  Error al leer .env: {e}")
    else:
        print("❌ El archivo .env NO existe en el directorio actual")
        print("   Posibles soluciones:")
        print("   • Copia el archivo .env desde desarrollo")
        print("   • Verifica que estés en el directorio correcto")
        print("   • Verifica permisos del archivo")

    # 3. Cargar variables de entorno
    print("\n🔄 Cargando variables de entorno...")
    load_dotenv()
    print("✓ load_dotenv() ejecutado")

    # 4. Verificar variables de entorno
    print("\n📋 Variables de entorno:")
    mail_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
    all_present = True

    for var in mail_vars:
        value = os.environ.get(var)
        status = "✓ Presente" if value else "✗ Ausente"
        if value and 'PASSWORD' not in var.upper():
            print(f"  {var}: {status} ({value})")
        else:
            print(f"  {var}: {status}")
        if not value:
            all_present = False

    # 5. Verificar otras variables importantes
    print("\n🔧 Otras variables de configuración:")
    other_vars = ['SERVER_NAME', 'PREFERRED_URL_SCHEME', 'TEST_SMTP_ON_STARTUP']
    for var in other_vars:
        value = os.environ.get(var, 'No definido')
        print(f"  {var}: {value}")

    # 6. Verificar conectividad básica
    print("\n🌐 Verificando conectividad:")
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        print("  ✓ Conexión a internet: OK")
    except:
        print("  ✗ Conexión a internet: FALLANDO")
        print("    Esto puede impedir el envío de emails")

    # 7. Verificar puerto SMTP
    print("\n📮 Verificando puerto SMTP (587):")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('smtp.gmail.com', 587))
        sock.close()
        if result == 0:
            print("  ✓ Puerto 587 accesible")
        else:
            print("  ✗ Puerto 587 bloqueado o inaccesible")
    except:
        print("  ✗ Error al verificar puerto 587")

    # 8. Resumen y recomendaciones
    print("\n" + "=" * 60)
    print("RESUMEN Y RECOMENDACIONES")
    print("=" * 60)

    if not os.path.exists(env_path):
        print("❌ PROBLEMA CRÍTICO: No se encuentra el archivo .env")
        print("   SOLUCIÓN: Copia el .env desde tu entorno de desarrollo")
    elif not all_present:
        print("❌ PROBLEMA: Variables de email faltantes")
        print("   SOLUCIÓN: Verifica que el .env tenga todas las variables necesarias")
        print("   MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER")
    else:
        print("✅ Configuración básica parece correcta")
        print("   Si aún hay problemas, verifica:")
        print("   • La contraseña de aplicación de Gmail")
        print("   • La autenticación de 2 factores")
        print("   • Los permisos del archivo .env")
        print("   • El directorio de trabajo de la aplicación")

    print("\n📝 Para ejecutar en producción:")
    print("   python diagnose_production.py")
    print("=" * 60)

if __name__ == "__main__":
    diagnose_email_config()