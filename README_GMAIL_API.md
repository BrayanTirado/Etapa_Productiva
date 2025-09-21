# Configuración de Gmail API para Envío de Emails

Esta guía explica cómo configurar Gmail API para el envío confiable de emails en producción, reemplazando SMTP.

## 🚀 **Ventajas de Gmail API vs SMTP**

- ✅ **Más confiable**: No depende de contraseñas de aplicación que expiran
- ✅ **Mejores límites**: Hasta 500 emails/día inicialmente, ampliable
- ✅ **Sin problemas de firewall**: Usa HTTPS (puerto 443) en lugar de SMTP (puerto 587)
- ✅ **Mejor debugging**: Logs detallados de Google
- ✅ **OAuth seguro**: Autenticación moderna y segura

## 📋 **Pasos de Configuración**

### **Paso 1: Instalar Dependencias**

```bash
pip install -r requirements.txt
```

### **Paso 2: Configurar Proyecto en Google Cloud Console**

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la **Gmail API**:
   - Ve a "APIs y servicios" > "Biblioteca"
   - Busca "Gmail API" y habilítala

### **Paso 3: Crear Credenciales OAuth 2.0**

1. Ve a "APIs y servicios" > "Credenciales"
2. Haz clic en "Crear credenciales" > "ID de cliente OAuth"
3. Selecciona "Aplicación web"
4. Configura:
   - **Nombre**: "SENA App"
   - **URIs de redireccionamiento autorizados**: `http://localhost:8080` (para desarrollo)
   - Para producción: Agrega tu dominio, ej: `https://senaproductiva.isladigital.xyz`
5. Descarga el archivo JSON y renómbralo como `credentials.json`
6. Coloca `credentials.json` en la raíz del proyecto

### **Paso 4: Configurar Autenticación**

Ejecuta el script de configuración:

```bash
python google_credentials_setup.py
```

Esto abrirá una ventana del navegador para autorizar la aplicación. Una vez autorizado, se creará `token.pickle` con las credenciales.

### **Paso 5: Configurar Variables de Entorno**

Asegúrate de que `.env` tenga:

```env
USE_GMAIL_API=true
```

### **Paso 6: Probar la Configuración**

```bash
python google_credentials_setup.py
```

Debería enviar un email de prueba exitosamente.

## 🔧 **Configuración para Producción**

### **Variables de Entorno en el Servidor**

```bash
export USE_GMAIL_API=true
```

### **Archivos Necesarios en Producción**

Sube estos archivos al servidor de producción:
- `credentials.json`
- `token.pickle` (generado después de la autenticación)

### **Autenticación en Producción**

Para producción, necesitas configurar OAuth con tu dominio. Actualiza las credenciales OAuth:

1. Ve a Google Cloud Console > Credenciales
2. Edita el ID de cliente OAuth
3. Agrega tu dominio de producción a "URIs de redireccionamiento autorizados"
4. Vuelve a ejecutar `google_credentials_setup.py` en el servidor de producción

## 🐛 **Solución de Problemas**

### **Error: "Credenciales no válidas"**
```bash
# Eliminar token antiguo y volver a autenticar
rm token.pickle
python google_credentials_setup.py
```

### **Error: "Gmail API has not been used"**
- Ve a Google Cloud Console y habilita Gmail API nuevamente

### **Error: "Access blocked"**
- Verifica que tu dominio esté autorizado en las credenciales OAuth
- Asegúrate de que la aplicación esté en "Producción" en Google Cloud Console

### **Error: "Daily limit exceeded"**
- Gmail API tiene límites diarios. Para aumentarlos, solicita verificación de aplicación en Google.

## 📊 **Límites de Gmail API**

- **Gratis**: 500 emails/día
- **Pago**: Hasta 10,000 emails/día inicialmente
- **Verificación completa**: Límites mucho más altos

## 🔄 **Fallback Automático**

El código está configurado para:
1. Intentar Gmail API primero
2. Si falla, usar SMTP como respaldo
3. Proporcionar logs detallados para debugging

## 📁 **Archivos de Configuración**

- `credentials.json`: Credenciales OAuth de Google
- `token.pickle`: Tokens de acceso (generado automáticamente)
- `.env`: Variables de entorno (USE_GMAIL_API=true)

## 🚀 **Implementación Rápida**

Para implementar rápidamente:

```bash
# 1. Instalar dependencias
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

# 2. Configurar credenciales
python google_credentials_setup.py

# 3. Configurar .env
echo "USE_GMAIL_API=true" >> .env

# 4. Probar
python -c "from app.routes.auth import send_reset_email; send_reset_email('tu-email@gmail.com', 'https://test.com')"
```

¡Listo! Ahora tienes un sistema de envío de emails mucho más confiable para producción.