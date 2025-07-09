
# Arquitectura de Agentes (Modelo Lógico)

Este documento describe la arquitectura del sistema desde una perspectiva de "agentes" o componentes lógicos. Es importante aclarar que estos agentes **no son procesos ni microservicios independientes**, sino una forma de organizar las responsabilidades dentro de una única aplicación Flask. Son módulos y clases de Python que colaboran para lograr la automatización.

## Diagrama de Interacción de Agentes

El siguiente diagrama muestra cómo estos componentes lógicos interactúan entre sí.

```mermaid
graph TD
    subgraph "Capa de Orquestación"
        A[OrchestrationService<br/>(bolsa_service.py)]
    end

    subgraph "Capa de Ejecución (Bot)"
        B[PageManager<br/>(bot_page_manager.py)]
        C[LoginManager<br/>(bot_login.py)]
        D[DataCaptureService<br/>(bot_data_capture.py)]
    end

    subgraph "Capa de Datos y Comunicación"
        E[(Database<br/>SQLAlchemy Models)]
        F[RealTimeSync<br/>(Flask-SocketIO)]
    end

    %% Flujos
    A -- "1. Inicia ejecución" --> B
    B -- "2. Obtiene/Crea Página" --> C
    C -- "3. Asegura Sesión" --> D
    D -- "4. Captura Datos" --> A
    A -- "5. Procesa y Almacena" --> E
    A -- "6. Notifica al Frontend" --> F

    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef data fill:#e8f4ff,stroke:#5a9bd5;
    class E,F data;
```

---

### 2. OrchestrationService (Capa de Orquestación)
- **Archivos**: `src/routes/api/bot_routes.py`, `src/tasks.py`
- **Responsabilidad**: Este no es un único agente, sino la capa lógica que decide **cómo y cuándo** se ejecutan las tareas de fondo. Implementa un **modelo de ejecución híbrido**:
    1.  **Ejecución en Hilo (para el Dashboard)**: Para las solicitudes interactivas del usuario (ej. "Actualizar precios"), utiliza `threading.Thread` para lanzar el `DataCaptureService` de forma inmediata en un hilo separado. Esto asegura una respuesta rápida en la UI sin bloquear el servidor web.
    2.  **Ejecución con Celery (para Tareas Pesadas)**: Para tareas no interactivas y de larga duración, como el análisis del "Drainer", encola una tarea en Redis para que sea procesada por un `Celery Worker`.
- **Inteligencia**: Su lógica principal es desacoplar las tareas largas del ciclo de vida de la petición HTTP.

### 3. DataCaptureService (Bot de Playwright)
**Archivo principal:** `src/scripts/bot_data_capture.py`

**Propósito:**
Este componente se especializa en la extracción de datos de la página una vez que la sesión está activa.

- **Captura de datos de red:** Su función principal, `capture_premium_data_via_network`, intercepta las peticiones de red que hace la página para obtener los datos de precios en formato JSON, evitando el scraping directo del HTML.
- **Captura de otros datos:** También obtiene información adicional, como la hora oficial del mercado (`capture_market_time`).
- **Validación:** Incluye una función para validar que el formato de los datos recibidos es el esperado (`validate_premium_data`).

## 5. RealTimeSync
**Implementación principal:** `Flask-SocketIO` (inicializado en `src/extensions.py`)

**Propósito:**
Actúa como el agente de comunicación en tiempo real entre el backend y el frontend.

- **Emisión de eventos:** El `OrchestrationService` lo utiliza para enviar eventos al cliente (`socketio.emit`). Los eventos clave son:
    - `update_complete`: Notifica que hay nuevos datos disponibles.
    - `bot_error`: Informa al usuario de un error durante el proceso de scraping.
    - `initial_session_ready`: Indica que el bot está listo para recibir peticiones por primera vez.

*(Nota: El antiguo `HARParserAgent` (`har_analyzer.py`) sigue existiendo en el código pero su rol en el flujo principal ha sido reemplazado por la captura de datos de red directa realizada por el `DataCaptureService`. Actualmente, podría considerarse una herramienta de depuración o un mecanismo de fallback).* 