
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
- `REDIS_URL` (Opcional): La URL de conexión a Redis. Si se usa Docker Compose, no es necesario definirla, ya que se inyecta automáticamente.

## 2. Entorno Contenerizado con Docker Compose

La aplicación está diseñada para funcionar de manera autocontenida utilizando Docker. El archivo `docker-compose.yml` orquesta todos los servicios necesarios para que la aplicación se ejecute con un solo comando.

### `docker-compose.yml`
Este archivo define tres servicios clave:

1.  **`app`**: El contenedor de la aplicación Flask.
    -   Construye la imagen de Docker a partir del `Dockerfile` local.
    -   Depende de que `db` y `redis` estén listos antes de iniciarse.
    -   Mapea el puerto `5000` para que puedas acceder a la aplicación desde tu navegador.
    -   Monta el código fuente actual en `/app` dentro del contenedor, permitiendo el desarrollo en vivo (los cambios en el código se reflejan sin necesidad de reconstruir la imagen).
    -   Inyecta las variables de entorno `DATABASE_URL` y `REDIS_URL` para que la aplicación se conecte a los otros contenedores.

2.  **`db`**: El contenedor de la base de datos (PostgreSQL + TimescaleDB).
    -   Utiliza la imagen oficial de TimescaleDB.
    -   Expone el puerto `5432` por si deseas conectarte con un cliente de base de datos externo.
    -   Utiliza un volumen persistente (`timescale_data`) para que los datos no se borren entre reinicios.
    -   Incluye un `healthcheck` para asegurar que la aplicación no intente conectarse hasta que la base de datos esté completamente lista.

3.  **`redis`**: El contenedor de Redis.
    -   Utiliza la imagen oficial de Redis.
    -   Expone el puerto `6379`.
    -   Configura un volumen persistente (`redis_data`).
    -   Tiene un `healthcheck` para verificar que el servicio esté activo.

### Uso: Iniciar todo el entorno

Con este enfoque, **no necesitas instalar Python, PostgreSQL o Redis en tu máquina local.** Solo necesitas Docker.

1.  Asegúrate de tener Docker y Docker Compose instalados y en ejecución.
2.  Crea tu archivo `.env` con las credenciales (`BOLSA_USERNAME` y `BOLSA_PASSWORD`).
3.  Abre una terminal en la raíz del proyecto.
4.  Ejecuta el comando:
    ```bash
    docker-compose up --build -d
    ```
5.  Este comando hará lo siguiente:
    -   **`--build`**: Construirá la imagen de Docker para la aplicación (`app`) la primera vez (o si el `Dockerfile` cambia).
    -   **`up`**: Creará e iniciará los tres contenedores (`app`, `db`, `redis`) en el orden correcto de dependencias.
    -   **`-d`**: Los ejecutará en segundo plano (detached mode).

Para detener todos los servicios, ejecuta: `docker-compose down`.

## 3. Gestión de Entornos (Desarrollo vs. Producción)

-   **Desarrollo (local con Docker)**:
    -   Es el método recomendado y descrito anteriormente.
    -   Crea tu archivo `.env`.
    -   Levanta todo con `docker-compose up --build -d`.
    -   Accede a la aplicación en `http://localhost:5000`.
    -   Los cambios en el código se reflejan automáticamente gracias al volumen montado.

-   **Producción**:
    -   El `docker-compose.yml` es una base excelente para producción.
    -   Las variables de entorno (especialmente las credenciales) deben ser inyectadas de forma segura por tu proveedor de nube o sistema de orquestación, en lugar de usar un archivo `.env`.
    -   Asegúrate de que el modo `DEBUG` de Flask esté desactivado.
    -   Se podría utilizar un servidor WSGI como Gunicorn en lugar del servidor de desarrollo de Flask (esto requeriría modificar el `CMD` en el `Dockerfile`). 