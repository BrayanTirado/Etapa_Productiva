#!/bin/bash
# Script automático para configurar Gmail API en producción
# Ejecutar una sola vez en el servidor de producción

echo "=== CONFIGURACIÓN AUTOMÁTICA GMAIL API - PRODUCCIÓN ==="

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
    echo "Descárgalo de Google Cloud Console y súbelo al servidor"
    exit 1
fi

if [ ! -f "token.pickle" ]; then
    echo "ERROR: Falta token.pickle"
    echo "Ejecuta: python google_credentials_setup.py"
    exit 1
fi

echo "Configuración completada exitosamente!"
echo "Reinicia la aplicación para usar Gmail API"
