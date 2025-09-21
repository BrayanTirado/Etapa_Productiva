#!/usr/bin/env python3
"""
Script simple para verificar configuración de email
Ejecuta: python check_email_simple.py
"""

import os
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

print("=== VERIFICACIÓN DE EMAIL ===")

# Verificar variables
vars_to_check = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']

for var in vars_to_check:
    value = os.environ.get(var)
    if value:
        if 'PASSWORD' in var:
            print(f"[OK] {var}: Configurado (***oculto***)")
        else:
            print(f"[OK] {var}: {value}")
    else:
        print(f"[ERROR] {var}: NO CONFIGURADO")

print("\n=== FIN VERIFICACIÓN ===")