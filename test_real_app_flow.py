#!/usr/bin/env python3
"""
Script que simula exactamente el flujo de la aplicación real
"""

import os
from dotenv import load_dotenv
from app import create_app

def test_real_app_flow():
    """Prueba el flujo real de la aplicación"""

    print("=" * 70)
    print("PRUEBA DEL FLUJO REAL DE LA APLICACIÓN")
    print("=" * 70)

    # Cargar variables de entorno
    load_dotenv()

    print(f"SERVER_NAME: {os.environ.get('SERVER_NAME')}")
    print(f"PREFERRED_URL_SCHEME: {os.environ.get('PREFERRED_URL_SCHEME')}")
    print(f"PROXY_FIX_ENABLED: {os.environ.get('PROXY_FIX_ENABLED')}")

    # Crear la aplicación real
    app = create_app()

    with app.app_context():
        print("\n[TEST] Probando flujo completo de forgot_password...")

        # Simular los datos del formulario
        email = 'stivenvargas1615@gmail.com'  # Usar el mismo email del usuario

        # Importar las funciones necesarias
        from app.routes.auth import find_user_by_email, generate_reset_token, send_reset_email
        from app.models.users import PasswordResetToken
        from flask import url_for
        from datetime import datetime, timedelta

        print(f"[FLOW] Buscando usuario por email: {email}")

        # Paso 1: Buscar usuario
        user, user_type = find_user_by_email(email)

        if not user:
            print(f"[ERROR] Usuario no encontrado: {email}")
            return False

        print(f"[OK] Usuario encontrado: {user_type}")

        # Paso 2: Generar token
        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        print(f"[TOKEN] Token generado: {token[:20]}...")
        print(f"[TIME] Expira: {expires_at}")

        # Paso 3: Crear registro en BD
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
            email=email,
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

        # Paso 4: Generar URL (este es el punto crítico)
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
                print("       Esto sugiere que el blueprint 'auth' no está registrado")
                print("       o que SERVER_NAME está causando conflictos")

                # Intentar con URL manual
                try:
                    manual_url = f"{os.environ.get('PREFERRED_URL_SCHEME', 'https')}://{os.environ.get('SERVER_NAME')}/auth/reset_password/{token}"
                    print(f"[FALLBACK] URL manual: {manual_url}")
                    reset_url = manual_url
                except Exception as e2:
                    print(f"[ERROR] Error en fallback: {e2}")
                    return False
            else:
                return False

        # Paso 5: Enviar email (este es el otro punto crítico)
        print(f"[EMAIL] Enviando email a: {email}")

        try:
            email_sent = send_reset_email(email, reset_url)

            if email_sent:
                print(f"[SUCCESS] Email enviado exitosamente a {email}")
                return True
            else:
                print(f"[WARNING] Email NO pudo enviarse a {email}")
                print("         Pero el token se guardó correctamente en BD")
                return False

        except Exception as e:
            print(f"[ERROR] Excepción durante envío de email: {e}")
            print(f"[ERROR] Tipo de error: {type(e).__name__}")

            import traceback
            print(f"[TRACEBACK] {traceback.format_exc()}")
            return False

if __name__ == "__main__":
    success = test_real_app_flow()

    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    if success:
        print("✅ FLUJO COMPLETO EXITOSO")
        print("   - Usuario encontrado")
        print("   - Token generado y guardado")
        print("   - URL generada correctamente")
        print("   - Email enviado exitosamente")
    else:
        print("❌ FLUJO FALLÓ")
        print("   Revisa los logs anteriores para identificar el problema")

    print("\n[SUGERENCIA] Si funciona aquí pero falla en producción:")
    print("   - Verifica que el .env esté disponible en el servidor")
    print("   - Verifica que las variables de entorno se carguen correctamente")
    print("   - Verifica que la aplicación se inicie completamente antes de procesar requests")
    print("   - Considera agregar más logging en producción")