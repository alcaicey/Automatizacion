
# Arquitectura de Alto Nivel

## 1. Descripción General

La aplicación sigue una **arquitectura monolítica con un componente de fondo desacoplado por hilos (threads)**. Consiste en cuatro componentes principales que trabajan en conjunto para entregar la funcionalidad de monitoreo de acciones.

- **Frontend**: Una interfaz de usuario web interactiva.
- **Backend**: Un servidor web basado en Flask que gestiona la lógica de negocio y la comunicación.
- **Bot de Scraping**: Un agente automatizado que se ejecuta en segundo plano para obtener los datos.
- **Base de Datos**: Un sistema de persistencia para almacenar todos los datos de la aplicación.

La comunicación en tiempo real entre el backend y el frontend se logra mediante **WebSockets**.

## 2. Componentes Principales

### 2.1. Frontend
- **Tecnologías**: HTML5, CSS3, JavaScript, Bootstrap, jQuery.
- **Responsabilidades**:
    - Presentar los datos de las acciones al usuario en una tabla interactiva.
    - Permitir al usuario configurar filtros, columnas y credenciales.
    - Enviar solicitudes al Backend para iniciar acciones (ej. actualizar datos).
    - Escuchar eventos de WebSocket para recibir actualizaciones de datos en tiempo real y actualizar la UI sin necesidad de recargar la página.

### 2.2. Backend (Servidor Flask)
- **Tecnologías**: Python, Flask, Flask-SocketIO, SQLAlchemy.
- **Responsabilidades**:
    - Servir los archivos estáticos y plantillas que componen el Frontend.
    - Exponer una **API REST** para gestionar las acciones del usuario (ej. `POST /api/stocks/update`).
    - Gestionar las conexiones **WebSocket** con los clientes para empujar datos nuevos.
    - Orquestar la ejecución del Bot de Scraping. Cuando una actualización es requerida, el backend inicia el bot en un **hilo separado** para no bloquear el servidor web principal.
    - Interactuar con la Base de Datos para persistir y consultar información (credenciales, historial de precios, etc.).

### 2.3. Bot de Scraping (Agente Playwright)
- **Tecnologías**: Python, Playwright, asyncio.
- **Responsabilidades**:
    - Es un módulo asíncrono (`asyncio`) que se ejecuta en su propio hilo.
    - Gestiona una instancia de un navegador (headless o no) a través de Playwright.
    - Realiza el login en el sitio web de la Bolsa de Santiago.
    - Navega a la página de datos y captura las solicitudes de red que contienen la información de precios de las acciones.
    - Procesa los datos capturados y los pasa directamente a la capa de persistencia (Base de Datos).
    - Su ejecución es controlada por un `asyncio.Lock` para asegurar que solo haya una instancia del bot corriendo a la vez.

### 2.4. Base de Datos
- **Tecnologías**: PostgreSQL, TimescaleDB.
- **Responsabilidades**:
    - Almacenar los datos de series temporales de los precios de las acciones. TimescaleDB está optimizado para este tipo de datos.
    - Guardar la configuración del usuario, como credenciales (de forma segura) y filtros de acciones.
    - Mantener un log de eventos y errores de la aplicación.
    - Guardar el historial de ejecuciones y comparativas de datos.

## 3. Diagrama de Flujo de Datos y Componentes

El siguiente diagrama ilustra cómo interactúan los componentes del sistema.

```mermaid
graph TD
    subgraph "Navegador del Usuario"
        Frontend[<B>Frontend</B><br/>HTML, JS, Bootstrap]
    end

    subgraph "Servidor de Aplicación (Proceso Flask)"
        Backend[<B>Backend</B><br/>API REST y WebSockets]
        
        subgraph "Hilo del Bot (Thread)"
            Bot[<B>Bot de Scraping</B><br/>Playwright & Asyncio]
        end
    end

    subgraph "Infraestructura"
        DB[(<B>Base de Datos</B><br/>PostgreSQL / TimescaleDB)]
    end

    subgraph "Internet"
        BolsaWebsite{Sitio Web<br/>Bolsa de Santiago}
    end

    %% Flujo de Usuario a Backend
    Frontend --"1. Petición HTTP (ej. 'Actualizar')"--> Backend

    %% Flujo de Websockets
    Backend --"5. Notificación de 'nuevos datos'"-.-> Frontend

    %% Flujo de ejecución del Bot
    Backend --"2. Inicia ejecución en hilo"--> Bot

    %% Flujo de scraping
    Bot --"3. Navega y extrae datos"--> BolsaWebsite

    %% Flujo de persistencia
    Bot --"4. Guarda datos extraídos"--> DB
    Backend --"Consultas y guardado de config."--> DB

```

## 4. Canales de Comunicación

- **HTTP/REST**: Utilizado por el frontend para enviar comandos al backend (comunicación iniciada por el cliente).
- **WebSocket**: Utilizado por el backend para empujar actualizaciones al frontend de forma proactiva (comunicación iniciada por el servidor).

## 5. Modelo de Ejecución y Escalabilidad

- **Modelo de Ejecución**: El bot de scraping es un módulo de `asyncio` que se ejecuta dentro de un `threading.Thread` gestionado por la aplicación Flask. Esto evita que las tareas de scraping, que son largas, bloqueen las respuestas a las peticiones web. Un `asyncio.Lock` previene ejecuciones concurrentes del bot.
- **Escalabilidad**: La arquitectura actual es **monolítica**. El escalado vertical (más CPU/RAM para la máquina que lo ejecuta) es la forma principal de mejorar el rendimiento. El escalado horizontal (múltiples instancias) es complejo debido al estado que gestiona el bot (la sesión del navegador). Para un verdadero escalado, el **Bot de Scraping debería ser extraído a un microservicio independiente** con una cola de trabajos (ej. RabbitMQ, Redis) para gestionar las tareas de actualización. 