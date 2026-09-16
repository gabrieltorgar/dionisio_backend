# Imagen ASGI de Dionisio: sirve la API REST y los WebSockets de la lotería.
# El despliegue serverless de Vercel (api/index.py, WSGI) NO soporta WebSockets;
# para las salas en tiempo real hay que correr este contenedor en un host con
# procesos persistentes (Render, Railway, Fly.io…).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    DJANGO_SETTINGS_MODULE=core.settings \
    PORT=8000

WORKDIR /app

# libpq y build-essential no hacen falta: psycopg2-binary trae la libpq.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Daphne habla HTTP y WebSocket sobre el mismo puerto.
CMD ["sh", "-c", "python src/manage.py migrate --noinput && daphne -b 0.0.0.0 -p ${PORT} --proxy-headers core.asgi:application"]
