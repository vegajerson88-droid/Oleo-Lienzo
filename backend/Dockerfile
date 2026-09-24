# ── Imagen del backend de Óleo & Lienzo ───────────────────────────────────
# Construir:  docker build -t oleo-lienzo-api ./backend
# Ejecutar:   docker run -p 8000:8000 --env-file backend/.env oleo-lienzo-api
FROM python:3.11-slim

# Evita los .pyc y fuerza la salida sin búfer, para ver los logs al instante.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Solo curl, para el HEALTHCHECK. No hace falta libpq5: psycopg[binary] trae
# su propia libpq dentro del paquete y enlaza contra ella, no contra la del
# sistema (comprobado con ldd sobre el módulo compilado).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Las dependencias se copian primero: así Docker reutiliza la capa mientras
# `requirements.txt` no cambie, aunque cambie el código.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# La aplicación no corre como root.
RUN useradd --create-home --shell /bin/bash oleo && chown -R oleo:oleo /app
USER oleo

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/sistema/salud || exit 1

# Railway y otras plataformas inyectan el puerto en $PORT.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
