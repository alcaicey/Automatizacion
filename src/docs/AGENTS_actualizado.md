
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

## 1. OrchestrationService
**Archivo principal:** `src/scripts/bolsa_service.py`

**Propósito:**
Es el cerebro y el punto de entrada para todas las operaciones de scraping. Orquesta las acciones de los demás componentes para realizar una actualización de datos de principio a fin.

- **Gestiona el ciclo de vida de la ejecución:** Utiliza un `asyncio.Lock` para garantizar que solo una instancia del bot se ejecute a la vez.
- **Orquesta la lógica de negocio:** Define la secuencia de pasos: chequear sesión, capturar datos, procesar y almacenar.
- **Maneja los reintentos y errores:** Implementa la lógica para reintentar la captura de datos y maneja las excepciones `LoginError` y `DataCaptureError`.
- **Interactúa con la capa de datos:** Llama a las funciones de `db_io.py` para guardar los precios en la base de datos.
- **Comunica con el frontend:** Emite eventos a través del `RealTimeSync` (Socket.IO) para notificar al cliente sobre el progreso, éxito o errores.

## 2. PageManager
**Archivo principal:** `src/scripts/bot_page_manager.py`

**Propósito:**
Administra el estado del navegador y la página de Playwright de forma centralizada y persistente. Su objetivo es evitar la sobrecarga de crear un nuevo navegador en cada ejecución.

- **Singleton de Playwright:** Mantiene una única instancia del navegador y la página (`Page`) a lo largo de la vida de la aplicación.
- **Gestión de estado:** Proporciona funciones para obtener la página actual (`get_page`) o para recrearla si se ha cerrado o corrompido (`recreate_page`).

## 3. LoginManager
**Archivo principal:** `src/scripts/bot_login.py`

**Propósito:**
Se encarga exclusivamente de la lógica de autenticación en el sitio web de la Bolsa.

- **Inicio de sesión automatizado:** Contiene la función `auto_login` que navega a la página de login, introduce las credenciales y completa el proceso.
- **Chequeo de sesión:** `bolsa_service.py` utiliza sus componentes para verificar si la sesión actual sigue siendo válida (`check_if_logged_in`) antes de intentar una captura de datos.

## 4. DataCaptureService
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