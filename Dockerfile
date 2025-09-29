FROM python:3.13-alpine 

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar requirements.txt e instalar dependencias
COPY requirements.txt .
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto que usará Gunicorn
EXPOSE 8080

# Ejecutar con Gunicorn en producción
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers=4", "--threads=2", "--forwarded-allow-ips=*", "wsgi:app"]
