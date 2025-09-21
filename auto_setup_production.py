#!/usr/bin/env python3
"""
Script de configuración automática para Gmail API en producción
Ejecutar UNA SOLA VEZ en el servidor de producción
No requiere intervención del usuario
"""

import os
import sys
import subprocess
import json

def run_command(command, description, show_output=False):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n[AUTO] {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] {description}")
            if show_output and result.stdout:
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"[ERROR] {description}")
            print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[ERROR] {description}: {e}")
        return False

def install_dependencies():
    """Instala todas las dependencias necesarias"""
    print("\n[AUTO] Instalando dependencias...")

    packages = [
        'google-api-python-client==2.115.0',
        'google-auth==2.29.0',
        'google-auth-oauthlib==1.2.0',
        'google-auth-httplib2==0.2.0'
    ]

    for package in packages:
        if not run_command(f"pip install {package}", f"Instalando {package}"):
            return False

    return True

def create_credentials_json():
    """Crea un archivo credentials.json básico si no existe"""
    if os.path.exists('credentials.json'):
        print("[OK] credentials.json ya existe")
        return True

    print("\n[AUTO] Creando credentials.json básico...")

    # Credenciales básicas (deberán ser reemplazadas por las reales)
    credentials_template = {
        "web": {
            "client_id": "your-client-id.apps.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "your-client-secret",
            "redirect_uris": [
                "http://localhost:8080",
                "https://senaproductiva.isladigital.xyz"
            ]
        }
    }

    try:
        with open('credentials.json', 'w') as f:
            json.dump(credentials_template, f, indent=2)
        print("[OK] credentials.json creado (debe ser configurado con credenciales reales)")
        print("[INFO] Reemplaza el contenido con las credenciales reales de Google Cloud Console")
        return True
    except Exception as e:
        print(f"[ERROR] Error creando credentials.json: {e}")
        return False

def create_token_pickle():
    """Crea un token.pickle básico si no existe"""
    if os.path.exists('token.pickle'):
        print("[OK] token.pickle ya existe")
        return True

    print("\n[AUTO] Creando token.pickle básico...")
    print("[INFO] Este archivo debe ser generado con credenciales OAuth válidas")
    print("[INFO] Ejecuta: python google_credentials_setup.py")

    # Crear archivo vacío que será sobrescrito
    try:
        with open('token.pickle', 'wb') as f:
            f.write(b'')  # Archivo vacío
        print("[OK] token.pickle creado (vacío - debe ser configurado)")
        return True
    except Exception as e:
        print(f"[ERROR] Error creando token.pickle: {e}")
        return False

def configure_env():
    """Configura variables de entorno"""
    print("\n[AUTO] Configurando variables de entorno...")

    env_vars = {
        'USE_GMAIL_API': 'true'
    }

    # Configurar en el sistema
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"[OK] {key}={value}")

    # También actualizar .env si existe
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'a') as f:
            f.write(f'\n# Gmail API Configuration\nUSE_GMAIL_API=true\n')
        print("[OK] .env actualizado")

    return True

def test_import():
    """Prueba que las importaciones funcionen"""
    print("\n[AUTO] Probando importaciones...")

    try:
        import google.auth
        import googleapiclient.discovery
        from app.routes.auth import send_reset_email
        print("[OK] Todas las importaciones funcionan")
        return True
    except ImportError as e:
        print(f"[ERROR] Error de importación: {e}")
        return False

def create_production_script():
    """Crea script para ejecutar en producción"""
    print("\n[AUTO] Creando script de producción...")

    script_content = '''#!/bin/bash
# Script automático para configurar Gmail API en producción
# Ejecutar una sola vez en el servidor de producción

echo "=== CONFIGURACIÓN AUTOMÁTICA GMAIL API - PRODUCCIÓN ==="

# Instalar dependencias
echo "Instalando dependencias..."
pip install google-api-python-client==2.115.0 google-auth==2.29.0 google-auth-oauthlib==1.2.0 google-auth-httplib2==0.2.0

# Configurar variables de entorno
echo "Configurando variables de entorno..."
export USE_GMAIL_API=true
echo "USE_GMAIL_API=true" >> ~/.bashrc

# Verificar archivos
echo "Verificando archivos de credenciales..."
if [ ! -f "credentials.json" ]; then
    echo "ERROR: Falta credentials.json"
    echo "Descárgalo de Google Cloud Console y súbelo al servidor"
    exit 1
fi

if [ ! -f "token.pickle" ]; then
    echo "ERROR: Falta token.pickle"
    echo "Ejecuta: python google_credentials_setup.py"
    exit 1
fi

echo "Configuración completada exitosamente!"
echo "Reinicia la aplicación para usar Gmail API"
'''

    try:
        with open('setup_production.sh', 'w', newline='\n') as f:
            f.write(script_content)
        os.chmod('setup_production.sh', 0o755)
        print("[OK] Script de producción creado: setup_production.sh")
        return True
    except Exception as e:
        print(f"[ERROR] Error creando script: {e}")
        return False

def main():
    """Configuración automática completa"""
    print("CONFIGURACIÓN AUTOMÁTICA GMAIL API")
    print("=" * 50)
    print("Este script configura todo lo necesario para Gmail API")
    print("Ejecutar una sola vez")

    success_count = 0
    total_steps = 6

    # Paso 1: Instalar dependencias
    if install_dependencies():
        success_count += 1
    else:
        print("\n[CRITICAL] Error instalando dependencias")
        return

    # Paso 2: Crear credentials.json
    if create_credentials_json():
        success_count += 1

    # Paso 3: Crear token.pickle
    if create_token_pickle():
        success_count += 1

    # Paso 4: Configurar entorno
    if configure_env():
        success_count += 1

    # Paso 5: Probar importaciones
    if test_import():
        success_count += 1

    # Paso 6: Crear script de producción
    if create_production_script():
        success_count += 1

    # Resultado final
    print("\n" + "=" * 50)
    print(f"RESULTADO: {success_count}/{total_steps} pasos completados")

    if success_count >= 5:
        print("\n[SUCCESS] Configuración automática completada!")
        print("\nPASOS SIGUIENTES:")
        print("1. Reemplaza credentials.json con tus credenciales reales de Google Cloud Console")
        print("2. Ejecuta: python google_credentials_setup.py (para generar token.pickle)")
        print("3. Para producción: copia setup_production.sh al servidor y ejecutalo")
        print("4. Reinicia tu aplicación")

        print("\nARCHIVOS CREADOS:")
        print("- credentials.json (configurar con credenciales reales)")
        print("- token.pickle (generar con OAuth)")
        print("- setup_production.sh (script para servidor)")
    else:
        print("\n[WARNING] Configuración incompleta")
        print("Revisa los errores y completa manualmente")

if __name__ == "__main__":
    main()