#!/usr/bin/env python3
"""
Script que simula exactamente lo que pasa en producción cuando un usuario
solicita recuperación de contraseña desde la aplicación web
"""

import os
from dotenv import load_dotenv
from app import create_app

def test_production_forgot_password():
    """Simula exactamente el flujo de forgot_password en producción"""

    print("=" * 80)
    print("SIMULACIÓN DE FORGOT_PASSWORD EN PRODUCCIÓN")
    print("=" * 80)

    # Cargar variables de entorno
    load_dotenv()

    print(f"SERVER_NAME: {os.environ.get('SERVER_NAME')}")
    print(f"PREFERRED_URL_SCHEME: {os.environ.get('PREFERRED_URL_SCHEME')}")
    print(f"PROXY_FIX_ENABLED: {os.environ.get('PROXY_FIX_ENABLED')}")

    # Crear la aplicación real
    app = create_app()

    # Simular un email de usuario real (NO pruebuno01@gmail.com)
    user_email = 'test-user@example.com'  # Email que un usuario real ingresaría

    with app.app_context():
        print(f"\n[TEST] Simulando solicitud de recuperación para: {user_email}")

        # Importar las funciones necesarias (exactamente como en la aplicación)
        from app.routes.auth import find_user_by_email, generate_reset_token, send_reset_email
        from app.models.users import PasswordResetToken
        from flask import url_for
        from datetime import datetime, timedelta

        # PASO 1: Buscar usuario por email (usando un email que sabemos que existe)
        # Para la prueba, usaremos el email del administrador que sabemos que existe
        test_email = 'stivenvargas1615@gmail.com'  # Email que existe en la BD

        print(f"[FLOW] Buscando usuario por email: {test_email}")

        user, user_type = find_user_by_email(test_email)

        if not user:
            print(f"[ERROR] Usuario no encontrado: {test_email}")
            print("   Nota: Este error es esperado si el usuario no existe en la BD de desarrollo")
            print("   En producción, este sería un email real de usuario")
            return False

        print(f"[OK] Usuario encontrado: {user_type}")

        # PASO 2: Generar token (exactamente como en la aplicación)
        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        print(f"[TOKEN] Token generado: {token[:20]}...")
        print(f"[TIME] Token expira: {expires_at}")

        # PASO 3: Crear registro en BD
        id_attr_map = {
            'aprendiz': 'id_aprendiz',
            'instructor': 'id_instructor',
            'coordinador': 'id_coordinador',
            'administrador': 'id_admin'
        }
        id_attr = id_attr_map.get(user_type, f'id_{user_type}')
        user_id = getattr(user, id_attr)

        reset_token = PasswordResetToken(
            token=token,
            email=test_email,  # Email del usuario que solicita recuperación
            user_type=user_type,
            user_id=user_id,
            expires_at=expires_at
        )

        try:
            from app import db
            db.session.add(reset_token)
            db.session.commit()
            print(f"[DB] Token guardado en BD - ID: {reset_token.id}")
        except Exception as e:
            print(f"[ERROR] Error guardando token en BD: {e}")
            db.session.rollback()
            return False

        # PASO 4: Generar URL de restablecimiento (CRÍTICO - aquí puede estar el problema)
        print(f"[URL] Generando URL de restablecimiento...")

        try:
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            print(f"[OK] URL generada: {reset_url}")
        except Exception as e:
            print(f"[ERROR] Error generando URL: {e}")
            print(f"[ERROR] Tipo de error: {type(e).__name__}")

            # Intentar diagnóstico
            if "Could not build url" in str(e):
                print("[DIAG] Problema con construcción de URL")
                print("       Esto sugiere que SERVER_NAME está causando conflictos")
                print("       En producción, esto podría impedir la generación de URLs")

                # Intentar con URL manual como fallback
                try:
                    manual_url = f"{os.environ.get('PREFERRED_URL_SCHEME', 'https')}://{os.environ.get('SERVER_NAME')}/auth/reset_password/{token}"
                    print(f"[FALLBACK] URL manual: {manual_url}")
                    reset_url = manual_url
                except Exception as e2:
                    print(f"[ERROR] Error en fallback: {e2}")
                    return False
            else:
                return False

        # PASO 5: Enviar email (AQUÍ ESTÁ EL PROBLEMA REAL)
        print(f"[EMAIL] Enviando email de recuperación a: {test_email}")
        print("        (En producción, este sería el email del usuario que solicita recuperación)")
        print(f"[EMAIL] URL del email: {reset_url}")

        try:
            email_sent = send_reset_email(test_email, reset_url)

            if email_sent:
                print(f"[SUCCESS] Email enviado exitosamente a {test_email}")
                print("         En producción, el usuario recibiría el email de recuperación")
                return True
            else:
                print(f"[FAILURE] Email NO pudo enviarse a {test_email}")
                print("          En producción, el usuario vería el mensaje de error")
                print("          'Hemos procesado tu solicitud, pero puede haber un problema temporal...'")
                return False

        except Exception as e:
            print(f"[ERROR] Excepción durante envío de email: {e}")
            print(f"[ERROR] Tipo de error: {type(e).__name__}")

            import traceback
            print(f"[TRACEBACK] {traceback.format_exc()}")
            return False

if __name__ == "__main__":
    success = test_production_forgot_password()

    print("\n" + "=" * 80)
    print("ANÁLISIS DEL RESULTADO")
    print("=" * 80)

    if success:
        print("✅ SIMULACIÓN EXITOSA")
        print("   - El flujo de forgot_password funciona correctamente")
        print("   - El email se enviaría al usuario en producción")
        print("   - El problema debe estar en el servidor de producción")
    else:
        print("❌ SIMULACIÓN FALLÓ")
        print("   - El problema se reproduce en desarrollo")
        print("   - Revisar logs anteriores para identificar la causa")

    print("\n" + "=" * 80)
    print("POSIBLES CAUSAS DEL PROBLEMA EN PRODUCCIÓN")
    print("=" * 80)
    print("1. Variables de entorno no disponibles en el servidor")
    print("2. Flask-Mail no inicializado correctamente en producción")
    print("3. Problemas de conectividad en el servidor de producción")
    print("4. Firewall bloqueando conexiones SMTP")
    print("5. Configuración de proxy causando problemas")
    print("6. Diferencias en el contexto de aplicación entre desarrollo y producción")

    print("\n" + "=" * 80)
    print("SOLUCIONES RECOMENDADAS")
    print("=" * 80)
    print("1. Ejecutar 'python diagnose_production_email.py' en el servidor de producción")
    print("2. Verificar que el archivo .env esté presente y tenga todas las variables")
    print("3. Revisar logs de la aplicación en producción durante el envío de email")
    print("4. Verificar que el servidor tenga acceso a internet y puerto 587")
    print("5. Considerar problemas de inicialización de Flask-Mail en el servidor")