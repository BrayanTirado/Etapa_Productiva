#!/usr/bin/env python3
"""
Script de instalación automática para Gmail API
Configura todo lo necesario para usar Gmail API en lugar de SMTP
Ejecutar una sola vez para configurar completamente
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n[SETUP] {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] {description} - Completado")
            return True
        else:
            print(f"[ERROR] {description} - Fallo")
            print(f"Detalle: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] {description} - Excepcion: {e}")
        return False

def check_requirements():
    """Verifica e instala las dependencias necesarias"""
    print("\n[SETUP] Verificando dependencias...")

    required_packages = [
        'google-api-python-client',
        'google-auth',
        'google-auth-oauthlib',
        'google-auth-httplib2'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"[OK] {package} - Instalado")
        except ImportError:
            missing_packages.append(package)
            print(f"[MISSING] {package} - Faltante")

    if missing_packages:
        print(f"\n[SETUP] Instalando paquetes faltantes: {', '.join(missing_packages)}")
        packages_str = ' '.join(missing_packages)
        if not run_command(f"pip install {packages_str}", "Instalando dependencias"):
            print("[ERROR] Error instalando dependencias. Instala manualmente:")
            print(f"pip install {packages_str}")
            return False

    return True

def setup_env_file():
    """Configura el archivo .env para usar Gmail API"""
    print("\n[SETUP] Configurando archivo .env...")

    env_file = '.env'
    gmail_api_line = 'USE_GMAIL_API=true'

    # Leer archivo .env si existe
    env_content = ""
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()

    # Verificar si ya está configurado
    if gmail_api_line in env_content:
        print("[OK] USE_GMAIL_API ya está configurado en .env")
        return True

    # Agregar la configuración
    if env_content and not env_content.endswith('\n'):
        env_content += '\n'

    env_content += f'\n# Configuración de envío de emails\n{gmail_api_line}\n'

    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("[OK] Archivo .env configurado correctamente")
        return True
    except Exception as e:
        print(f"[ERROR] Error configurando .env: {e}")
        return False

def check_credentials_files():
    """Verifica si existen los archivos de credenciales"""
    print("\n[SETUP] Verificando archivos de credenciales...")

    files_status = {
        'credentials.json': 'Credenciales OAuth de Google (descargar de Google Cloud Console)',
        'token.pickle': 'Tokens de acceso (generado automáticamente)'
    }

    all_present = True

    for file_name, description in files_status.items():
        if os.path.exists(file_name):
            print(f"[OK] {file_name} - Presente")
        else:
            print(f"[MISSING] {file_name} - Ausente")
            print(f"   Info: {description}")
            all_present = False

    return all_present

def run_setup_script():
    """Ejecuta el script de configuración de credenciales"""
    print("\n[SETUP] Ejecutando configuración de credenciales OAuth...")

    if not os.path.exists('google_credentials_setup.py'):
        print("[ERROR] Archivo google_credentials_setup.py no encontrado")
        return False

    print("Se abrirá una ventana del navegador para autorizar la aplicación.")
    print("Sigue las instrucciones en el navegador.")
    print("Presiona Enter para continuar...")
    input()

    try:
        result = subprocess.run([sys.executable, 'google_credentials_setup.py'],
                              capture_output=False, text=True)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n[WARNING] Configuración interrumpida por el usuario")
        return False
    except Exception as e:
        print(f"[ERROR] Error ejecutando configuración: {e}")
        return False

def test_email_sending():
    """Prueba el envío de un email"""
    print("\n[SETUP] Probando envío de email...")

    # Importar la función de envío
    try:
        sys.path.append('.')
        from app.routes.auth import send_reset_email

        # Email de prueba (cambiar por tu email)
        test_email = os.environ.get('MAIL_DEFAULT_SENDER', 'pruebuno01@gmail.com')
        test_url = 'https://senaproductiva.isladigital.xyz/auth/reset_password/test-token'

        print(f"Enviando email de prueba a: {test_email}")

        if send_reset_email(test_email, test_url):
            print("[SUCCESS] Email enviado correctamente")
            return True
        else:
            print("[WARNING] Error enviando email, pero puede ser normal en primera configuración")
            return False

    except Exception as e:
        print(f"[ERROR] Error en la prueba: {e}")
        return False

def create_production_files():
    """Crea archivos necesarios para producción"""
    print("\n[SETUP] Preparando archivos para producción...")

    # Crear script de despliegue para producción
    production_script = '''#!/bin/bash
# Script de despliegue para producción - Gmail API
# Ejecutar en el servidor de producción

echo "=== DESPLIEGUE GMAIL API EN PRODUCCIÓN ==="

# Instalar dependencias
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

# Configurar variables de entorno
export USE_GMAIL_API=true

# Verificar archivos de credenciales
if [ ! -f "credentials.json" ]; then
    echo "ERROR: Falta credentials.json"
    exit 1
fi

if [ ! -f "token.pickle" ]; then
    echo "ERROR: Falta token.pickle - ejecuta configuración OAuth primero"
    exit 1
fi

echo "Configuración completada. Reinicia la aplicación."
'''

    try:
        with open('deploy_production.sh', 'w', newline='\n') as f:
            f.write(production_script)
        os.chmod('deploy_production.sh', 0o755)
        print("[OK] Script de despliegue creado: deploy_production.sh")
        return True
    except Exception as e:
        print(f"[ERROR] Error creando script de despliegue: {e}")
        return False

def main():
    """Función principal de instalación"""
    print("INSTALACIÓN AUTOMÁTICA DE GMAIL API")
    print("=" * 50)

    success_count = 0
    total_steps = 6

    # Paso 1: Verificar dependencias
    if check_requirements():
        success_count += 1
    else:
        print("\n[CRITICAL] Fallo en instalación de dependencias")
        return

    # Paso 2: Configurar .env
    if setup_env_file():
        success_count += 1
    else:
        print("\n[CRITICAL] Fallo en configuración de .env")
        return

    # Paso 3: Verificar archivos de credenciales
    if check_credentials_files():
        success_count += 1
        print("\n[OK] Todos los archivos de credenciales están presentes")
    else:
        print("\n[WARNING] Faltan archivos de credenciales. Debes obtenerlos:")
        print("1. Ve a https://console.cloud.google.com/")
        print("2. Crea proyecto y habilita Gmail API")
        print("3. Crea credenciales OAuth 2.0")
        print("4. Descarga credentials.json")
        print("5. Ejecuta: python google_credentials_setup.py")

    # Paso 4: Configurar credenciales (solo si faltan)
    if not os.path.exists('token.pickle'):
        if run_setup_script():
            success_count += 1
        else:
            print("\n[WARNING] Configuración OAuth no completada")
    else:
        print("\n[OK] Credenciales ya configuradas")
        success_count += 1

    # Paso 5: Probar envío
    if test_email_sending():
        success_count += 1
    else:
        print("\n[WARNING] Prueba de envío fallida, pero configuración puede estar correcta")

    # Paso 6: Crear archivos de producción
    if create_production_files():
        success_count += 1

    # Resultado final
    print("\n" + "=" * 50)
    print(f"RESULTADO: {success_count}/{total_steps} pasos completados")

    if success_count >= 5:
        print("SUCCESS: Instalación completada exitosamente")
        print("Gmail API está configurado y listo para usar")
        print("\nPara producción:")
        print("1. Copia credentials.json y token.pickle al servidor")
        print("2. Ejecuta: bash deploy_production.sh")
        print("3. Reinicia la aplicación")
    else:
        print("WARNING: Instalación incompleta")
        print("Revisa los errores arriba y completa los pasos faltantes")

    print("\nArchivos importantes:")
    print("- credentials.json: Credenciales OAuth")
    print("- token.pickle: Tokens de acceso")
    print("- deploy_production.sh: Script para servidor de producción")

if __name__ == "__main__":
    main()