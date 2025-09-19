#!/usr/bin/env python3
"""
Script de diagnóstico para verificar el estado de los tokens de recuperación de contraseña
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db
    from app.models.users import PasswordResetToken

    def diagnose_tokens():
        """Diagnóstico completo de tokens"""

        print("DIAGNOSTICO DE TOKENS DE RECUPERACION DE CONTRASENA")
        print("=" * 60)

        app = create_app()

        with app.app_context():
            # Verificar conexión a BD
            print("Verificando conexion a base de datos...")
            try:
                db.engine.execute("SELECT 1")
                print("Conexion a BD exitosa")
            except Exception as e:
                print(f"Error de conexion a BD: {e}")
                return

            # Verificar tabla
            print("\\nVerificando tabla 'password_reset_token'...")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            if 'password_reset_token' in tables:
                print("Tabla 'password_reset_token' existe")
            else:
                print("Tabla 'password_reset_token' NO existe")
                print(f"Tablas disponibles: {tables}")
                print("Creando tablas...")
                db.create_all()
                print("Tablas creadas")

            # Contar tokens
            print("\\nEstadisticas de tokens:")
            total_tokens = PasswordResetToken.query.count()
            used_tokens = PasswordResetToken.query.filter_by(used=True).count()
            unused_tokens = PasswordResetToken.query.filter_by(used=False).count()

            print(f"   - Total de tokens: {total_tokens}")
            print(f"   - Tokens usados: {used_tokens}")
            print(f"   - Tokens sin usar: {unused_tokens}")

            # Mostrar tokens recientes
            if total_tokens > 0:
                print("\\nUltimos 5 tokens:")
                recent_tokens = PasswordResetToken.query.order_by(PasswordResetToken.created_at.desc()).limit(5).all()

                for i, token in enumerate(recent_tokens, 1):
                    print(f"   {i}. Token: {token.token[:20]}...")
                    print(f"      Email: {token.email}")
                    print(f"      Tipo: {token.user_type}")
                    print(f"      Usado: {token.used}")
                    print(f"      Creado: {token.created_at}")
                    print(f"      Expira: {token.expires_at}")
                    print(f"      Expirado: {token.is_expired()}")
                    print()

            # Verificar configuración de zona horaria
            print("\\nVerificacion de zona horaria:")
            from datetime import datetime
            now_utc = datetime.utcnow()
            print(f"   - Hora actual (UTC): {now_utc}")

            # Probar creación de token
            print("\\nPrueba de creacion de token:")
            try:
                test_token = PasswordResetToken(
                    token="test_token_12345",
                    email="test@example.com",
                    user_type="administrador",
                    user_id=1,
                    expires_at=datetime.utcnow()
                )
                db.session.add(test_token)
                db.session.commit()
                print("Token de prueba creado exitosamente")

                # Verificar que se puede recuperar
                found_token = PasswordResetToken.query.filter_by(token="test_token_12345").first()
                if found_token:
                    print("Token de prueba recuperado exitosamente")
                else:
                    print("Token de prueba NO se pudo recuperar")

                # Limpiar token de prueba
                db.session.delete(test_token)
                db.session.commit()
                print("Token de prueba limpiado")

            except Exception as e:
                print(f"Error al crear token de prueba: {e}")
                db.session.rollback()

    if __name__ == "__main__":
        diagnose_tokens()

except ImportError as e:
    print(f"Error de importacion: {e}")
    print("Asegurate de tener instaladas todas las dependencias")
except Exception as e:
    print(f"Error inesperado: {e}")
    import traceback
    traceback.print_exc()