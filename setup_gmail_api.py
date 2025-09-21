#!/usr/bin/env python3
"""
Script de instalación rápida para Gmail API
Configura todo lo necesario para usar Gmail API en lugar de SMTP
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
    """Verifica que las dependencias estén instaladas"""
    print("\n📦 Verificando dependencias...")

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
            print(f"✅ {package} - Instalado")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - Faltante")

    if missing_packages:
        print(f"\n🔄 Instalando paquetes faltantes: {', '.join(missing_packages)}")
        packages_str = ' '.join(missing_packages)
        if not run_command(f"pip install {packages_str}", "Instalando dependencias"):
            print("❌ Error instalando dependencias. Instala manualmente:")
            print(f"pip install {packages_str}")
            return False

    return True

def setup_env_file():
    """Configura el archivo .env para usar Gmail API"""
    print("\n📝 Configurando archivo .env...")

    env_file = '.env'
    gmail_api_line = 'USE_GMAIL_API=true'

    # Leer archivo .env si existe
    env_content = ""
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()

    # Verificar si ya está configurado
    if gmail_api_line in env_content:
        print("✅ USE_GMAIL_API ya está configurado en .env")
        return True

    # Agregar la configuración
    if env_content and not env_content.endswith('\n'):
        env_content += '\n'

    env_content += f'\n# Configuración de envío de emails\n{gmail_api_line}\n'

    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Archivo .env configurado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error configurando .env: {e}")
        return False

def check_credentials_files():
    """Verifica si existen los archivos de credenciales"""
    print("\n🔐 Verificando archivos de credenciales...")

    files_status = {
        'credentials.json': 'Credenciales OAuth de Google (descargar de Google Cloud Console)',
        'token.pickle': 'Tokens de acceso (generado automáticamente)'
    }

    all_present = True

    for file_name, description in files_status.items():
        if os.path.exists(file_name):
            print(f"✅ {file_name} - Presente")
        else:
            print(f"❌ {file_name} - Ausente")
            print(f"   Info: {description}")
            all_present = False

    return all_present

def run_setup_script():
    """Ejecuta el script de configuración de credenciales"""
    print("\n🚀 Ejecutando configuración de credenciales...")

    if not os.path.exists('google_credentials_setup.py'):
        print("❌ Archivo google_credentials_setup.py no encontrado")
        return False

    print("Ejecutando configuración OAuth...")
    print("Se abrirá una ventana del navegador para autorizar la aplicación.")
    print("Sigue las instrucciones en el navegador.")
    print()

    try:
        result = subprocess.run([sys.executable, 'google_credentials_setup.py'],
                              capture_output=False, text=True)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n⚠️  Configuración interrumpida por el usuario")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando configuración: {e}")
        return False

def test_email_sending():
    """Prueba el envío de un email"""
    print("\n📧 Probando envío de email...")

    # Importar la función de envío
    try:
        sys.path.append('.')
        from app.routes.auth import send_reset_email

        # Email de prueba (cambiar por tu email)
        test_email = os.environ.get('MAIL_DEFAULT_SENDER', 'pruebuno01@gmail.com')
        test_url = 'https://senaproductiva.isladigital.xyz/auth/reset_password/test-token'

        print(f"Enviando email de prueba a: {test_email}")

        if send_reset_email(test_email, test_url):
            print("✅ Email enviado correctamente")
            return True
        else:
            print("❌ Error enviando email")
            return False

    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        return False

def main():
    """Función principal de instalación"""
    print("🚀 INSTALACIÓN RÁPIDA DE GMAIL API")
    print("=" * 50)

    success_count = 0
    total_steps = 5

    # Paso 1: Verificar dependencias
    if check_requirements():
        success_count += 1
    else:
        print("\n❌ Instalación fallida en el paso 1")
        return

    # Paso 2: Configurar .env
    if setup_env_file():
        success_count += 1
    else:
        print("\n❌ Instalación fallida en el paso 2")
        return

    # Paso 3: Verificar archivos de credenciales
    if check_credentials_files():
        success_count += 1
        print("\n✅ Todos los archivos de credenciales están presentes")
    else:
        print("\n⚠️  Faltan archivos de credenciales. Debes obtenerlos manualmente:")
        print("1. Ve a https://console.cloud.google.com/")
        print("2. Crea/usa un proyecto existente")
        print("3. Habilita Gmail API")
        print("4. Crea credenciales OAuth 2.0")
        print("5. Descarga credentials.json")
        print("6. Ejecuta: python google_credentials_setup.py")

    # Paso 4: Configurar credenciales (solo si faltan)
    if not os.path.exists('token.pickle'):
        if run_setup_script():
            success_count += 1
        else:
            print("\n⚠️  Configuración de credenciales no completada")
    else:
        print("\n✅ Credenciales ya configuradas")
        success_count += 1

    # Paso 5: Probar envío
    if test_email_sending():
        success_count += 1
    else:
        print("\n⚠️  Prueba de envío fallida, pero la configuración puede estar correcta")

    # Resultado final
    print("\n" + "=" * 50)
    print(f"RESULTADO: {success_count}/{total_steps} pasos completados")

    if success_count >= 4:
        print("✅ INSTALACIÓN EXITOSA")
        print("Gmail API está configurado y listo para usar en producción")
        print("\nPara usar en producción:")
        print("1. Sube credentials.json y token.pickle al servidor")
        print("2. Configura USE_GMAIL_API=true en el .env del servidor")
        print("3. Reinicia la aplicación")
    else:
        print("⚠️  INSTALACIÓN INCOMPLETA")
        print("Revisa los errores arriba y completa los pasos faltantes")

if __name__ == "__main__":
    main()