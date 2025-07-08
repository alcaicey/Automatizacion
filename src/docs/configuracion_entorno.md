
# Guía de Configuración del Entorno

Este documento explica cómo configurar el entorno de desarrollo y producción para la aplicación, incluyendo las variables de entorno, la base de datos Dockerizada y otras dependencias.

## 1. Variables de Entorno y el Archivo `.env`

La aplicación se configura mediante variables de entorno. La forma recomendada de gestionarlas en un entorno de desarrollo es a través de un archivo `.env` ubicado en la raíz del proyecto.

**Nunca debes subir tu archivo `.env` a un repositorio Git.**

### Archivo de Ejemplo (`.env.example`)
Para empezar, crea un archivo llamado `.env` en la raíz del proyecto. Puedes usar el siguiente contenido como plantilla:

```ini
# -----------------------------------------------------------------------------
# ARCHIVO DE VARIABLES DE ENTORNO (.env)
# -----------------------------------------------------------------------------
# Completa los valores requeridos para tu configuración local.

# --- Credenciales (Obligatorias) ---
# Usuario y contraseña para acceder al sitio web de la Bolsa de Santiago.
BOLSA_USERNAME="tu_usuario_de_la_bolsa"
BOLSA_PASSWORD="tu_contraseña_de_la_bolsa"

# --- Configuración de la Base de Datos (Opcional) ---
# URL de conexión para la base de datos.
# Si usas el docker-compose.yml, el valor por defecto en el código es suficiente.
# DATABASE_URL="postgresql://postgres:postgres@localhost:5432/bolsa"

# --- Configuración del Servidor (Opcional) ---
# Puerto para el servidor web de Flask. Por defecto es 5000.
FLASK_PORT=5000
```

### Detalle de las Variables
- `BOLSA_USERNAME` (Obligatoria): Tu nombre de usuario para el sitio de la Bolsa.
- `BOLSA_PASSWORD` (Obligatoria): Tu contraseña para el sitio de la Bolsa.
- `DATABASE_URL` (Opcional): La cadena de conexión a la base de datos. Si no se provee, la aplicación usará `postgresql://postgres:postgres@localhost:5432/bolsa`, que es el valor por defecto para el servicio de Docker.
- `FLASK_PORT` (Opcional): El puerto en el que correrá la aplicación Flask. Por defecto es `5000`.
- `BOLSA_SCRIPTS_DIR` / `BOLSA_LOGS_DIR` (Opcional): Variables avanzadas para redirigir las carpetas de scripts y logs. No se recomienda modificarlas.

## 2. Base de Datos con Docker Compose

La aplicación está diseñada para funcionar con una base de datos PostgreSQL con la extensión TimescaleDB. La forma más sencilla de levantarla es usando Docker.

### `docker-compose.yml`
El archivo `docker-compose.yml` en la raíz del proyecto define el servicio de la base de datos.

```yaml
services:
  db:
    image: timescale/timescaledb:latest-pg15
    container_name: bolsa_timescaledb
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=bolsa
    ports:
      - "5432:5432"
    volumes:
      - timescale_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d bolsa"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  timescale_data:
```
- **`image`**: Usa la imagen oficial de TimescaleDB para Postgres 15.
- **`environment`**: Configura el usuario, contraseña y nombre de la base de datos inicial. Estos valores coinciden con la `DATABASE_URL` por defecto de la aplicación.
- **`ports`**: Mapea el puerto 5432 del contenedor al puerto 5432 de tu máquina local.
- **`volumes`**: Crea un volumen persistente (`timescale_data`) para que los datos no se pierdan si el contenedor se reinicia.
- **`healthcheck`**: Docker revisa periódicamente si la base de datos está lista para aceptar conexiones, lo cual es útil para orquestaciones más complejas.

### Uso
1. Asegúrate de tener Docker y Docker Compose instalados y en ejecución.
2. Abre una terminal en la raíz del proyecto.
3. Ejecuta el comando: `docker-compose up -d`
4. Esto iniciará el contenedor de la base de datos en segundo plano. La primera vez puede tardar unos minutos mientras se descarga la imagen.

## 3. Gestión de Entornos (Desarrollo vs. Producción)

La aplicación no tiene un mecanismo formal para distinguir entre entornos, pero se puede adoptar una estrategia estándar:

- **Desarrollo (local)**:
    - Usa el archivo `.env` para cargar las variables.
    - Ejecuta la base de datos con `docker-compose up -d`.
    - Inicia la aplicación directamente con `python src/main.py`.

- **Producción (sugerencia)**:
    - **No usar el modo debug de Flask.**
    - Las variables de entorno no deberían cargarse desde un archivo `.env`, sino que deben ser **provistas directamente por el sistema operativo o el orquestador de contenedores** (ej. Heroku, AWS ECS, Kubernetes).
    - La aplicación Flask debería ser ejecutada por un servidor WSGI de producción como **Gunicorn** o **uWSGI** para mayor rendimiento y estabilidad.
    - El `docker-compose.yml` podría extenderse para incluir el servicio de la aplicación (`web`), construyendo una imagen de Docker a partir del `Dockerfile` del proyecto (que habría que crear). 