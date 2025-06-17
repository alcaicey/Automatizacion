# Documentación de la Aplicación de Filtro de Acciones

## Descripción General

Esta aplicación web permite filtrar y visualizar datos de acciones de la Bolsa de Santiago en tiempo real. La aplicación utiliza un script de scraping con Playwright para obtener los datos, los almacena en una base de datos TimescaleDB y los presenta en una interfaz de usuario intuitiva y responsiva con actualizaciones en tiempo real a través de WebSockets.

## Características Principales

1.  **Backend Robusto con Flask**:
    *   API RESTful para la gestión de datos, credenciales, filtros y configuraciones.
    *   Integración con SQLAlchemy para el mapeo de objetos a la base de datos.
    *   Servidor WebSocket con Flask-SocketIO para notificaciones en tiempo real al frontend.

2.  **Scraping y Automatización con Playwright**:
    *   Módulo `bolsa_santiago_bot.py` que automatiza el login y la captura de datos de la red.
    *   Gestor de página (`page_manager.py`) que mantiene una sesión persistente del navegador para evitar logins repetidos.
    *   Orquestador (`bolsa_service.py`) que coordina la ejecución del bot y el almacenamiento de datos.

3.  **Persistencia de Datos**:
    *   Uso de PostgreSQL con la extensión TimescaleDB, optimizada para datos de series temporales (precios de acciones).
    *   Modelos de datos para acciones, credenciales, logs, filtros y preferencias de usuario.
    *   Fallback a archivos JSON para historial y comparación si la base de datos no está disponible.

4.  **Frontend Interactivo**:
    *   Interfaz responsiva construida con Bootstrap.
    *   Filtrado de acciones por código, con persistencia de la configuración.
    *   Actualización manual de datos con un solo clic.
    *   Planificador de actualizaciones automáticas (intervalos aleatorios).
    *   Visualización de datos con indicadores de cambio (colores y flechas).
    *   Configuración de columnas visibles en la tabla de datos.
    *   Página de visualización de la arquitectura de la aplicación con diagramas Mermaid.js.

## Estructura del Proyecto (Refactorizada)
bolsa_app/
├── src/
│ ├── automatizacion_bolsa/
│ │ ├── page_manager.py # Gestión centralizada del navegador y sesiones
│ │ └── data_capture.py # Lógica para capturar datos de la red
│ ├── models/ # Modelos de datos SQLAlchemy
│ ├── routes/
│ │ └── api.py # Endpoints de la API RESTful
│ ├── scripts/
│ │ ├── bolsa_santiago_bot.py # Bot que ejecuta la automatización de Playwright
│ │ └── bolsa_service.py # Orquestador principal del scraping y almacenamiento
│ ├── static/
│ │ ├── app.js # Lógica JS principal del frontend
│ │ └── historico.js # JS para la vista de historial y comparación
│ ├── templates/
│ │ ├── index.html # Interfaz principal de la aplicación
│ │ ├── architecture.html # Página de visualización de la arquitectura
│ │ └── historico.html # Página para ver historial y comparaciones
│ ├── utils/
│ │ ├── db_io.py # Lógica de lectura/escritura en la base de datos
│ │ ├── json_utils.py # Utilidades para manejo de archivos JSON
│ │ ├── scheduler.py # Planificador de tareas periódicas
│ │ └── bot_control.py # Proxy para evitar importaciones circulares
│ ├── main.py # Punto de entrada de la aplicación Flask
│ └── config.py # Configuración centralizada
├── requirements.txt # Dependencias del proyecto
├── docker-compose.yml # Configuración para la base de datos TimescaleDB
└── README.md # Esta documentación

## Requisitos

- Python 3.11 o superior
- Docker y Docker Compose (para la base de datos)
- Un navegador web moderno

## Variables de Entorno

Es **obligatorio** definir las siguientes variables de entorno para que la aplicación funcione:

-   `BOLSA_USERNAME`: Usuario para el sitio de la Bolsa de Santiago.
-   `BOLSA_PASSWORD`: Contraseña para el sitio de la Bolsa de Santiago.
-   `DATABASE_URL`: Cadena de conexión para la base de datos. Por defecto, si usas `docker-compose.yml`, será `postgresql://postgres:postgres@localhost:5432/bolsa`.

## Instalación y Ejecución

1.  **Clonar y preparar el entorno**:
    ```bash
    # Clonar el repositorio
    git clone <url_del_repositorio>
    cd <directorio_del_proyecto>

    # Crear y activar un entorno virtual
    python -m venv venv
    # En Windows:
    venv\Scripts\activate
    # En Linux/macOS:
    source venv/bin/activate

    # Instalar dependencias de Python
    pip install -r requirements.txt
    ```

2.  **Instalar dependencias de Playwright**:
    ```bash
    # Instalar las dependencias del sistema operativo para los navegadores
    python -m playwright install-deps
    # Instalar los navegadores que usará Playwright (Chromium, etc.)
    python -m playwright install
    ```

3.  **Iniciar la Base de Datos**:
    Asegúrate de que Docker esté en ejecución.
    ```bash
    docker-compose up -d db
    ```
    La primera vez, esto descargará la imagen de TimescaleDB y creará un contenedor con una base de datos persistente.

4.  **Configurar las variables de entorno**:
    Crea un archivo `.env` en la raíz del proyecto o exporta las variables directamente en tu terminal.
    ```
    BOLSA_USERNAME="tu_usuario"
    BOLSA_PASSWORD="tu_contraseña"
    DATABASE_URL="postgresql://postgres:postgres@localhost:5432/bolsa"
    ```

5.  **Ejecutar la aplicación**:
    ```bash
    # Cargar variables de entorno si usas un archivo .env (necesitas python-dotenv)
    # pip install python-dotenv
    # (El main.py ya lo carga si existe)
    
    python src/main.py
    ```

6.  **Acceder a la aplicación**:
    -   Abre tu navegador y ve a `http://localhost:5000`.
    -   La primera vez, serás redirigido a `login.html` para ingresar y guardar tus credenciales. Si marcas "Recordar", se almacenarán en la base de datos y se cargarán automáticamente en futuros inicios.
    -   Una vez configuradas las credenciales, podrás acceder directamente a la página principal.

## Uso

-   **Filtrar Acciones**: Ingresa hasta 5 códigos de acciones y haz clic en "Filtrar".
-   **Actualizar Datos**: Haz clic en "Actualizar" para forzar una nueva ejecución del bot. El proceso se ejecuta en segundo plano.
-   **Actualización Automática**: Selecciona un intervalo en el menú desplegable para que la aplicación busque nuevos datos periódicamente.
-   **Historial**: Ve a la página de "Histórico" para ver un resumen de las cargas de datos y una comparación detallada entre las dos últimas.
-   **Arquitectura**: Visita la página de "Arquitectura" para ver diagramas del flujo de datos y componentes de la aplicación.
