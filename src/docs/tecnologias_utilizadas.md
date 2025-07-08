
# Dependencias y Tecnologías Utilizadas

Este documento proporciona un análisis de las tecnologías, frameworks y librerías clave que componen la aplicación.

## 1. Backend (Python)

El backend está construido sobre un stack de Python moderno, orquestado por las siguientes tecnologías principales.

- **Flask**: Es el micro-framework web sobre el que se construye toda la aplicación. Se encarga de gestionar las rutas (endpoints), renderizar las plantillas HTML y manejar las peticiones HTTP.
  - *Archivos clave: `src/main.py`, `src/routes/`*

- **SQLAlchemy**: Actúa como el ORM (Object-Relational Mapper), traduciendo las clases de Python (definidas en `src/models/`) a tablas en la base de datos. Facilita todas las interacciones con la base de datos de una manera orientada a objetos.
  - *Archivos clave: `src/models/`, `src/utils/db_io.py`*

- **Flask-SocketIO**: Una extensión de Flask que habilita la comunicación bidireccional y en tiempo real entre el servidor y el cliente mediante WebSockets. Es fundamental para empujar las actualizaciones de precios al frontend sin que el usuario necesite recargar la página.
  - *Archivos clave: `src/extensions.py`, `src/scripts/bolsa_service.py`*

- **Playwright**: Es la herramienta de automatización de navegadores utilizada para el web scraping. Permite al bot controlar un navegador real (Chromium en este caso), iniciar sesión, navegar y capturar datos de la red de forma programática. Se utiliza de forma asíncrona (`asyncio`) para un rendimiento óptimo.
  - *Archivos clave: `src/scripts/bot_*.py`*

- **Psycopg2**: El adaptador (driver) de base de datos para PostgreSQL en Python. Es el puente que permite a SQLAlchemy comunicarse con la base de datos.

- **Pytest**: Es el framework utilizado para las pruebas unitarias y de integración del backend, asegurando la calidad y fiabilidad del código.
  - *Archivos clave: `tests/`*

## 2. Frontend (Navegador)

El frontend se basa en una combinación de librerías y frameworks de JavaScript y CSS, cargados principalmente a través de CDNs.

- **Bootstrap**: El framework CSS principal que proporciona un diseño responsivo, componentes de UI pre-construidos (botones, modales, navbar) y un sistema de rejilla (grid system).
  - *Archivo clave: `src/templates/base.html`*

- **jQuery**: Aunque es una librería más tradicional, se utiliza aquí principalmente como una dependencia requerida por DataTables.

- **DataTables**: Una potente librería de JavaScript que mejora las tablas HTML estándar con funcionalidades avanzadas como paginación, búsqueda, ordenación y filtrado del lado del cliente.
  - *Archivo clave: `src/static/js/pages/dashboard.js`*

- **Socket.IO Client**: La librería de JavaScript que se conecta al servidor Flask-SocketIO. Se encarga de recibir los eventos en tiempo real (ej. `new_data`) y disparar las actualizaciones en la UI.
  - *Archivo clave: `src/static/js/app.js`*

- **Font Awesome**: Utilizada para incluir iconos en toda la interfaz de usuario, mejorando la experiencia visual.

## 3. Base de Datos

- **PostgreSQL**: Es el sistema de gestión de bases de datos relacional de código abierto sobre el que se construye la persistencia de datos.

- **TimescaleDB**: Es una extensión para PostgreSQL que lo optimiza para manejar datos de series temporales. Se utiliza para convertir la tabla `stock_prices` en una **hypertable**, lo que mejora drásticamente el rendimiento de las inserciones y las consultas basadas en rangos de tiempo.
  - *Archivo clave: `src/models/stock_price.py`*

## 4. Entorno y Herramientas (DevOps)

- **Docker y Docker Compose**: Se utilizan para crear un entorno de desarrollo consistente y aislado, específicamente para ejecutar la base de datos PostgreSQL/TimescaleDB en un contenedor. Esto asegura que todos los desarrolladores trabajen con la misma versión de la base de datos.
  - *Archivo clave: `docker-compose.yml`*

- **Vitest / Jest**: Frameworks de testing de JavaScript mencionados en `package.json`, utilizados para realizar pruebas unitarias sobre la lógica del frontend.
  - *Archivos clave: `package.json`, `tests/js/`* 