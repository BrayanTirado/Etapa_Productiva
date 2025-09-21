#!/usr/bin/env python3
"""
Script para probar las correcciones de email
Ejecuta: python test_email_fix.py
"""

import os
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# Simular el contexto de Flask
class MockConfig:
    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        # Simular que las variables NO están en current_app.config (como en producción)
        return None

# Simular current_app.config
mock_config = MockConfig()

def get_mail_config(key, default=None):
    """Función auxiliar igual a la del código corregido"""
    value = mock_config.get(key)
    if value is None:
        # Intentar cargar desde .env si no está en config
        load_dotenv()
        value = os.environ.get(key, default)
    return value

print("=== PRUEBA DE CORRECCIONES DE EMAIL ===")

# Probar obtener configuración con el nuevo método
mail_server = get_mail_config('MAIL_SERVER', 'smtp.gmail.com')
mail_port = get_mail_config('MAIL_PORT', 587)
mail_username = get_mail_config('MAIL_USERNAME')
mail_password = get_mail_config('MAIL_PASSWORD')
mail_default_sender = get_mail_config('MAIL_DEFAULT_SENDER', mail_username)

print("Configuración obtenida:")
print(f"  MAIL_SERVER: {mail_server}")
print(f"  MAIL_PORT: {mail_port}")
print(f"  MAIL_USERNAME: {mail_username}")
print(f"  MAIL_PASSWORD: {'***OCULTO***' if mail_password else 'None'}")
print(f"  MAIL_DEFAULT_SENDER: {mail_default_sender}")

if mail_username and mail_password and mail_default_sender:
    print("\n[SUCCESS] Todas las variables de email están disponibles")
    print("   Las correcciones deberían funcionar correctamente")
else:
    print("\n[ERROR] Faltan variables de email")
    print("   MAIL_USERNAME:", "OK" if mail_username else "FALTA")
    print("   MAIL_PASSWORD:", "OK" if mail_password else "FALTA")
    print("   MAIL_DEFAULT_SENDER:", "OK" if mail_default_sender else "FALTA")

print("\n=== FIN PRUEBA ===")