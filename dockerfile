# 1. Usamos la imagen oficial de uv para extraer el binario
FROM ghcr.io/astral-sh/uv:latest AS uv_bin

# 2. Imagen base de Python
FROM python:3.11-slim

# Configuración de Python y uv
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_PREFERENCE=only-system


WORKDIR /app

# Instalamos dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el binario de uv desde la primera etapa
COPY --from=uv_bin /uv /uvx /bin/

# --- OPTIMIZACIÓN DE CACHÉ ---
# Copiamos solo los archivos de dependencias primero
COPY pyproject.toml uv.lock /app/

# Instalamos las dependencias sin el proyecto (solo librerías)
# Esto se cacheará a menos que cambies el lockfile
RUN uv sync --frozen --no-install-project

# Ahora copiamos el resto del código
COPY . /app

# Instalamos el proyecto actual
RUN uv sync --frozen

# Añadimos el venv al PATH para no tener que usar 'uv run' siempre
ENV PATH="/app/.venv/bin:$PATH"

# Comando de ejecución
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]