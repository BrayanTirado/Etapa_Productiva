#!/usr/bin/env python3
"""
Configuración de credenciales para Gmail API
Ejecutar una vez para configurar las credenciales de Google API
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Si modificas estos scopes, elimina el archivo token.pickle
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def setup_google_credentials():
    """
    Configura las credenciales de Google API para Gmail
    """
    print("=" * 60)
    print("CONFIGURACIÓN DE CREDENCIALES GOOGLE API")
    print("=" * 60)

    creds = None
    # El archivo token.pickle almacena los tokens de acceso y refresco del usuario
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # Si no hay credenciales válidas disponibles, permite que el usuario inicie sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Verificar que existe el archivo credentials.json
            if not os.path.exists('credentials.json'):
                print("[ERROR] Archivo 'credentials.json' no encontrado")
                print()
                print("PASOS PARA OBTENER credentials.json:")
                print("1. Ve a https://console.developers.google.com/")
                print("2. Crea un nuevo proyecto o selecciona uno existente")
                print("3. Habilita la Gmail API")
                print("4. Ve a 'Credenciales' y crea credenciales OAuth 2.0")
                print("5. Descarga el archivo JSON y renómbralo como 'credentials.json'")
                print("6. Coloca el archivo en la raíz del proyecto")
                return False

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Guarda las credenciales para la próxima ejecución
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    print("[OK] Credenciales configuradas correctamente")
    return True

def test_gmail_api():
    """
    Prueba el envío de un email usando Gmail API
    """
    print("\n" + "=" * 50)
    print("PRUEBA DE ENVÍO CON GMAIL API")
    print("=" * 50)

    try:
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            print("[ERROR] Credenciales no válidas. Ejecuta setup_google_credentials() primero")
            return False

        service = build('gmail', 'v1', credentials=creds)

        # Crear mensaje de prueba
        import base64
        from email.mime.text import MIMEText

        message = MIMEText('Este es un email de prueba enviado usando Gmail API desde la aplicación SENA.')
        message['to'] = 'pruebuno01@gmail.com'  # Cambiar por tu email
        message['subject'] = 'Prueba Gmail API - SENA'

        # Codificar el mensaje
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}

        # Enviar el mensaje
        sent_message = service.users().messages().send(userId='me', body=body).execute()

        print(f"[SUCCESS] Email enviado correctamente. ID del mensaje: {sent_message['id']}")
        print("[INFO] Revisa tu bandeja de entrada")

        return True

    except Exception as e:
        print(f"[ERROR] Error enviando email con Gmail API: {e}")
        return False

def main():
    print("CONFIGURACIÓN DE GMAIL API PARA ENVÍO DE EMAILS")
    print()

    # Paso 1: Configurar credenciales
    if not setup_google_credentials():
        return

    # Paso 2: Probar envío
    if test_gmail_api():
        print("\n[SUCCESS] Gmail API configurado y probado correctamente")
        print("Ahora puedes usar Gmail API en lugar de SMTP")
    else:
        print("\n[ERROR] Error en la configuración de Gmail API")

if __name__ == "__main__":
    main()