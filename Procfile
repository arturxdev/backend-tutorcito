web: uvicorn core.asgi:application --host 0.0.0.0 --port $PORT
worker: python manage.py run_huey -w 4