#!/bin/bash
# Script autom�tico para configurar Gmail API en producci�n
# Ejecutar una sola vez en el servidor de producci�n

echo "=== CONFIGURACI�N AUTOM�TICA GMAIL API - PRODUCCI�N ==="

# Instalar dependencias
echo "Instalando dependencias..."
pip install google-api-python-client==2.115.0 google-auth==2.29.0 google-auth-oauthlib==1.2.0 google-auth-httplib2==0.2.0

# Configurar variables de entorno
echo "Configurando variables de entorno..."
export USE_GMAIL_API=true
echo "USE_GMAIL_API=true" >> ~/.bashrc

# Verificar archivos
echo "Verificando archivos de credenciales..."
if [ ! -f "credentials.json" ]; then
    echo "ERROR: Falta credentials.json"
    echo "Desc�rgalo de Google Cloud Console y s�belo al servidor"
    exit 1
fi

if [ ! -f "token.pickle" ]; then
    echo "ERROR: Falta token.pickle"
    echo "Ejecuta: python google_credentials_setup.py"
    exit 1
fi

echo "Configuraci�n completada exitosamente!"
echo "Reinicia la aplicaci�n para usar Gmail API"
