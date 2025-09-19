#!/usr/bin/env python3
"""
Script para probar la funcionalidad de recuperación de contraseña
con logging detallado para diagnosticar problemas.
"""

import time
import urllib.parse
import urllib.request

def test_password_reset():
    """Prueba completa del flujo de recuperación de contraseña"""

    print("Iniciando pruebas de recuperacion de contrasena...")

    # Paso 1: Enviar solicitud de recuperación
    print("\\nPaso 1: Enviando solicitud de recuperacion...")
    data = {'email': 'test@example.com'}
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')

    try:
        req = urllib.request.Request('http://127.0.0.1:8080/auth/forgot_password', data=encoded_data, method='POST')
        with urllib.request.urlopen(req) as response:
            print(f"Solicitud enviada - Status: {response.getcode()}")

    except Exception as e:
        print(f"Error en solicitud: {e}")
        return

    # Esperar un momento para que se procese
    time.sleep(2)

    # Paso 2: Probar una URL de ejemplo (necesitas obtener el token real de los logs del servidor)
    print("\\nPaso 2: INSTRUCCIONES PARA PRUEBA MANUAL")
    print("1. Revisa los logs del servidor Flask para ver el token generado")
    print("2. Copia el token completo de los logs")
    print("3. Prueba la URL: http://127.0.0.1:8080/auth/reset_password/[TOKEN_AQUI]")
    print("4. Si ves 'El enlace de restablecimiento no es valido', hay un problema")
    print("5. Si ves 'Restablecer Contrasena', funciona correctamente")

    print("\\nPaso 3: Verificacion de posibles problemas")
    print("- Asegurate de que el servidor Flask este corriendo")
    print("- Verifica que el email 'test@example.com' exista en la base de datos")
    print("- Revisa los logs del servidor para mensajes de error")
    print("- Confirma que la zona horaria este configurada correctamente")

if __name__ == "__main__":
    test_password_reset()