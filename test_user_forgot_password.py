#!/usr/bin/env python3
"""
Script que simula exactamente lo que pasa cuando un usuario solicita
recuperación de contraseña desde la aplicación web con un email REAL
"""

import os
from dotenv import load_dotenv
from app import create_app

def test_user_forgot_password():
    """Simula exactamente el flujo de forgot_password con email de usuario real"""

    print("=" * 80)
    print("PRUEBA DE FORGOT_PASSWORD CON EMAIL DE USUARIO REAL")
    print("=" * 80)

    # Cargar variables de entorno
    load_dotenv()

    print(f"SERVER_NAME: {os.environ.get('SERVER_NAME')}")
    print(f"PREFERRED_URL_SCHEME: {os.environ.get('PREFERRED_URL_SCHEME')}")
    print(f"PROXY_FIX_ENABLED: {os.environ.get('PROXY_FIX_ENABLED')}")

    # Crear la aplicación real
    app = create_app()

    # Email que un usuario real ingresaría (NO pruebuno01@gmail.com)
    # Usamos un email de prueba que no sea el de configuración
    user_email = 'usuario.prueba@example.com'  # Email que un usuario real pondría

    with app.app_context():
        print(f"\n[TEST] Simulando solicitud de recuperación para: {user_email}")
        print("        (Este sería el email que un usuario real ingresa en el formulario)")

        # PASO 1: Simular que el usuario existe
        # Para la prueba, crearemos un usuario ficticio o usaremos uno existente
        # Como no podemos crear usuarios reales, simularemos el flujo

        print(f"[FLOW] Verificando si el usuario existe...")

        # En la aplicación real, aquí se buscaría el usuario
        # Para la prueba, asumiremos que existe y continuamos

        print(f"[OK] Usuario verificado (simulado)")

        # PASO 2: Generar token (exactamente como en la aplicación)
        from app.routes.auth import generate_reset_token
        from datetime import datetime, timedelta

        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        print(f"[TOKEN] Token generado: {token[:20]}...")
        print(f"[TIME] Token expira: {expires_at}")

        # PASO 3: Simular guardado en BD (no lo haremos realmente para no contaminar)
        print(f"[DB] Token se guardaría en BD (simulado)")

        # PASO 4: Generar URL de restablecimiento
        print(f"[URL] Generando URL de restablecimiento...")

        try:
            from flask import url_for
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            print(f"[OK] URL generada: {reset_url}")
        except Exception as e:
            print(f"[ERROR] Error generando URL: {e}")
            print("       Intentando con URL manual...")
            reset_url = f"{os.environ.get('PREFERRED_URL_SCHEME', 'https')}://{os.environ.get('SERVER_NAME')}/auth/reset_password/{token}"
            print(f"[FALLBACK] URL manual: {reset_url}")

        # PASO 5: Enviar email al usuario real (AQUÍ ESTÁ EL PROBLEMA)
        print(f"[EMAIL] Enviando email de recuperación a: {user_email}")
        print("        (Este debería ser el email que recibe el usuario)")
        print(f"[EMAIL] URL del email: {reset_url}")

        try:
            from app.routes.auth import send_reset_email

            print("\n" + "="*60)
            print("ENVIANDO EMAIL AL USUARIO REAL...")
            print("="*60)

            email_sent = send_reset_email(user_email, reset_url)

            if email_sent:
                print(f"\n[SUCCESS] Email enviado exitosamente a {user_email}")
                print("          Si este script funciona, el problema está en producción")
                print("          El email debería llegar a la bandeja del usuario")
                return True
            else:
                print(f"\n[FAILURE] Email NO pudo enviarse a {user_email}")
                print("           Este es el mismo problema que ocurre en producción")
                print("           El usuario vería: 'Hemos procesado tu solicitud, pero puede haber un problema temporal...'")
                return False

        except Exception as e:
            print(f"\n[ERROR] Excepción durante envío de email: {e}")
            print(f"[ERROR] Tipo de error: {type(e).__name__}")

            import traceback
            print(f"[TRACEBACK] {traceback.format_exc()}")
            return False

if __name__ == "__main__":
    success = test_user_forgot_password()

    print("\n" + "=" * 80)
    print("ANÁLISIS DEL RESULTADO")
    print("=" * 80)

    if success:
        print("[OK] SIMULACIÓN EXITOSA")
        print("   - El flujo de forgot_password funciona correctamente")
        print("   - El email se enviaría al usuario real")
        print("   - El problema debe estar específicamente en el servidor de producción")
        print("   - Verifica que el .env esté presente en producción")
        print("   - Verifica que las variables de entorno se carguen correctamente")
        print("   - Revisa los logs de la aplicación en producción")
    else:
        print("[ERROR] SIMULACIÓN FALLÓ")
        print("   - El problema se reproduce incluso en desarrollo")
        print("   - Revisa la configuración SMTP y conectividad")

    print("\n" + "=" * 80)
    print("PRÓXIMOS PASOS PARA PRODUCCIÓN")
    print("=" * 80)
    print("1. Copia el archivo .env al servidor de producción")
    print("2. Reinicia la aplicación en producción")
    print("3. Prueba forgot_password con un email real desde la aplicación web")
    print("4. Si aún falla, ejecuta: python diagnose_production_email.py en el servidor")
    print("5. Revisa los logs de la aplicación en producción durante el envío")