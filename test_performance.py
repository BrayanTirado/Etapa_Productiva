#!/usr/bin/env python3
"""
Script para probar el rendimiento de las consultas de recuperación de contraseña
"""

import time
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_query_performance():
    """Prueba el rendimiento de las consultas de tokens"""

    print("=== PRUEBA DE RENDIMIENTO DE CONSULTAS ===")

    try:
        from app import create_app, db
        from app.models.users import PasswordResetToken
        from datetime import datetime, timedelta
        import secrets

        app = create_app()

        with app.app_context():
            print("\\n1. Verificando conexión a BD...")
            start_time = time.time()

            # Prueba de conexión simple
            db.session.execute(db.text("SELECT 1"))
            connection_time = time.time() - start_time
            print(f"Conexión exitosa en {connection_time:.2f}s")
            # Crear token de prueba
            print("\\n2. Creando token de prueba...")
            token_str = secrets.token_urlsafe(32)
            test_token = PasswordResetToken(
                token=token_str,
                email="performance@test.com",
                user_type="administrador",
                user_id=1,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )

            db.session.add(test_token)
            db.session.commit()
            print("Token de prueba creado")

            # Prueba de búsqueda con diferentes métodos
            print("\\n3. Probando métodos de búsqueda...")

            # Método 1: ORM estándar
            start_time = time.time()
            found_orm = PasswordResetToken.query.filter_by(token=token_str, used=False).first()
            orm_time = time.time() - start_time
            print(f"ORM time: {orm_time:.2f}s")

            # Método 2: SQL directo
            start_time = time.time()
            from sqlalchemy import text
            result = db.session.execute(text("""
                SELECT id, token, email, user_type, user_id, created_at, expires_at, used
                FROM password_reset_token
                WHERE token = :token AND used = 0
                LIMIT 1
            """), {'token': token_str}).first()

            sql_time = time.time() - start_time
            print(f"SQL time: {sql_time:.2f}s")

            # Comparación
            if orm_time < sql_time:
                print(f"Mejor rendimiento: ORM ({orm_time:.2f}s vs {sql_time:.2f}s)")
            else:
                print(f"Mejor rendimiento: SQL ({sql_time:.2f}s vs {orm_time:.2f}s)")
            # Limpiar token de prueba
            print("\\n4. Limpiando...")
            db.session.delete(test_token)
            db.session.commit()
            print("Token de prueba eliminado")

            print("\\n=== RESULTADOS ===")
            print(f"Tiempo de conexión: {connection_time:.2f}s")
            print(f"Tiempo ORM: {orm_time:.2f}s")
            print(f"Tiempo SQL: {sql_time:.2f}s")

            if connection_time > 5:
                print("\\nADVERTENCIA: La conexión a BD es lenta")
                print("   Considera usar SQLite local como fallback")
            else:
                print("\\nConexion a BD aceptable")

    except Exception as e:
        print(f"Error en prueba de rendimiento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query_performance()