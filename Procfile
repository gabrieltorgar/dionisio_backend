# Hosts tipo Heroku/Railway: un solo proceso ASGI para API + WebSockets.
web: python src/manage.py migrate --noinput && daphne -b 0.0.0.0 -p $PORT --proxy-headers core.asgi:application
