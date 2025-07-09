# Documentación Detallada del Proyecto de Automatización Financiera

## 1. Descripción General y Arquitectura

La aplicación es un sistema de monitoreo y análisis financiero centrado en la Bolsa de Santiago. Su propósito es automatizar la captura de datos del mercado, procesarlos, almacenarlos y presentarlos de forma útil, además de realizar análisis avanzados sobre ellos.

- **Backend**: Construido con **Flask** (Python), sirve una API RESTful para la gestión de datos y se comunica con el frontend en tiempo real mediante **Flask-SocketIO**.
- **Frontend**: Interfaz web interactiva que permite a los usuarios visualizar datos, configurar filtros y ver análisis.
- **Base de Datos**: **PostgreSQL** con la extensión **TimescaleDB**, optimizada para manejar grandes volúmenes de datos de series temporales como los precios de las acciones.
- **Captura de Datos**: Un bot automatizado con **Playwright** que navega el sitio web de la Bolsa de Santiago, se autentica y captura datos directamente de las llamadas de red (APIs internas del sitio), lo que lo hace robusto y preciso.

---

## 2. El Bot de Automatización: Funcionamiento Interno

El corazón de la aplicación es un bot construido con Playwright, diseñado para ser robusto, resiliente y para simular un comportamiento humano con el fin de evitar sistemas de detección de bots. A continuación se detalla su funcionamiento.

### 2.1. Proceso de Inicio de Sesión (`auto_login`)

El login es un proceso de varios pasos que gestiona múltiples casos borde.

**Estrategias Clave:**

-   **Comportamiento Humano**: El bot no interactúa instantáneamente con la página. Utiliza funciones `type_like_human` y `click_like_human` que introducen pausas aleatorias antes y después de cada acción, como hacer clic o rellenar un campo, para simular la cadencia de un usuario real.
-   **Lógica de Reintentos**: Todo el proceso de login está envuelto en un bucle que se ejecuta hasta 3 veces si se produce un error recuperable (como un timeout o un cierre inesperado de la página).

**Flujo de Ejecución Detallado:**

1.  **Navegación Inicial**: El bot navega a la página principal (`bolsadesantiago.com`) y espera a que la red esté inactiva (`networkidle`), una señal de que la página ha cargado completamente.
2.  **Detección de Anti-Bot**: Comprueba si la URL actual contiene `validate.perfdrive.com`, que corresponde a un sistema de CAPTCHA/anti-bot. Si lo detecta, espera un tiempo aleatorio largo (10-15s) y reinicia el proceso de login desde el principio.
3.  **Navegación al Formulario**:
    -   Espera a que el enlace de "Login" sea visible en la cabecera.
    -   Si la página está en modo responsivo (móvil), primero hace clic en el botón "toggler" para expandir el menú.
    -   Hace clic en el enlace de "Login" y luego en el botón "Ingresar" de la página intermedia.
4.  **Ingreso de Credenciales**: Rellena el usuario y la contraseña en el formulario de SSO (Single Sign-On).
5.  **Envío y Espera**: Envía el formulario y espera a que la página siguiente cargue.
6.  **Manejo de Sesiones Múltiples**:
    -   Tras el login, el sitio puede redirigir a una página que informa de sesiones activas en otros dispositivos (`plus_dispositivos_conectados`).
    -   El bot detecta esta URL, busca el botón para "Cerrar todas las sesiones" y lo presiona.
    -   Si esto ocurre, el flujo de login se reinicia para asegurar una sesión limpia.
7.  **Finalización Exitosa**: Si todos los pasos anteriores se completan sin errores, el proceso se considera exitoso y la función devuelve el control con una página autenticada.

### 2.2. Orquestación y Captura de Datos (`tasks.py` y `bot_routes.py`)

La ejecución del bot ya no se gestiona con un hilo local, sino que se ha desacoplado a través de un sistema de tareas en segundo plano con Celery y Redis, lo que mejora la robustez y escalabilidad.

**Flujo de Ejecución Detallado:**

1.  **Solicitud de Actualización**:
    -   El usuario inicia el proceso a través de una llamada a la API (ej. `POST /api/bot/start`).
    -   El controlador de la ruta en `bot_routes.py` no ejecuta el bot directamente. En su lugar, **encola una tarea** para Celery usando `start_bot_instance.delay()`.
    -   Responde inmediatamente al cliente con un mensaje de "tarea aceptada", sin esperar a que el scraping termine.

2.  **Ejecución por parte del Worker**:
    -   Un proceso **Celery Worker**, que se ejecuta de forma independiente, detecta la nueva tarea en la cola de Redis.
    -   El worker ejecuta la función `start_bot_instance` definida en `tasks.py`.
    -   Esta función contiene la lógica principal que antes estaba en `run_bolsa_bot`.

3.  **Chequeo de Salud de la Sesión (`perform_session_health_check`)**:
    -   Antes de capturar datos, el bot verifica si la sesión de Playwright sigue siendo válida.
    -   Navega a la página principal y busca un elemento del DOM que solo aparece cuando un usuario está logueado.
    -   Si la sesión no es válida, llama a `auto_login` para re-autenticarse.
    -   Una vez logueado, navega explícitamente a la página de datos (`plus_acciones_precios`) y verifica que se muestre el indicador de "Tiempo Real" para confirmar el acceso a datos premium.

4.  **Captura de Datos (`_attempt_data_capture`)**:
    -   Esta es la fase central. El bot no lee datos del HTML (scraping tradicional), sino que **intercepta las comunicaciones de red** que la página realiza con su propio backend.
    -   Inicia dos tareas de escucha de red de forma concurrente: una para la `hora del mercado` y otra para los `datos de precios`.
    -   Para activar estas llamadas de red, el bot **recarga la página**.
    -   Espera a que ambas respuestas de red sean capturadas.

5.  **Resiliencia y Casos Borde en la Captura**:
    -   **Reintentos**: Si la captura de datos falla (por ejemplo, por un timeout), el proceso se reintenta hasta 3 veces con pausas crecientes entre intentos.
    -   **Página Cerrada**: Si en algún momento la página es cerrada (posiblemente por el sistema anti-bot), el bot la recrea y continúa el proceso.
    -   **Fallback de Hora**: Si no logra interceptar la hora del mercado, utiliza la hora actual del sistema como respaldo (`get_fallback_market_time`) para no perder la actualización.

6.  **Validación y Almacenamiento**:
    -   Una vez que los datos JSON son capturados, una función de validación simple (`validate_premium_data`) comprueba que tengan la estructura esperada.
    -   Si todo es correcto, los datos y el timestamp se envían a la función `store_prices_in_db` para ser guardados en la base de datos.

---

## 3. Fuentes de Datos y Proceso de Captura

La aplicación no consume una API pública, sino que simula ser un cliente de la plataforma web de la Bolsa de Santiago.

### Fuentes Principales:

| Funcionalidad | URL de la Página | Endpoint de la API Interceptada | Script Responsable |
| :--- | :--- | :--- | :--- |
| **Precios de Acciones** | `.../plus_acciones_precios` | `api/RV_ResumenMercado/getAccionesPrecios` | `bolsa_service.py` |
| **Precios Premium** | `.../plus_acciones_precios` | `api/Cuenta_Premium/getPremiumAccionesPrecios`| `bolsa_service.py` |
| **Dividendos** | `.../dividendos` | `api/RV_ResumenMercado/getDividendos` | `dividend_service.py` |
| **Precios de Cierre** | `.../cierre_bursatil` | `api/RV_ResumenMercado/getCierreBursatilAnterior`| `closing_service.py` |
| **Hora del Mercado** | (Cualquier página logueada) | `api/Comunes/getHoraMercado` | `bot_data_capture.py` |

### Proceso de Captura (`bolsa_service.py`):

1.  **Orquestación**: La función `run_bolsa_bot` gestiona todo el proceso.
2.  **Gestión de Sesión**: Se asegura de que exista una sesión de usuario válida en la página, y si no, realiza un login automático.
3.  **Captura de Datos**: De forma concurrente, recarga la página de datos y escucha las respuestas de la red para capturar el JSON de precios y la hora oficial del mercado.
4.  **Resiliencia**: El sistema tiene reintentos (hasta 3) en caso de que la captura de datos falle.
5.  **Almacenamiento**: Los datos crudos en formato JSON son pasados al módulo `db_io.py` para ser procesados y guardados.

---

## 4. Base de Datos: Tablas y Columnas

A continuación se detalla el esquema de la base de datos, tabla por tabla.

### `stock_prices` (Hypertable)
Almacena los precios de las acciones capturados en tiempo real. Es una *hypertable* de TimescaleDB particionada por `timestamp` para un rendimiento óptimo.

| Columna | Tipo de Dato | Descripción |
| :--- | :--- | :--- |
| `symbol` | `String(50)` | **PK**. Código de la acción (Nemo). |
| `timestamp` | `DateTime` | **PK**. Fecha y hora de la captura del dato. |
| `price` | `Float` | Precio de cierre o último precio transado. |
| `variation` | `Float` | Variación porcentual del precio. |
| `buy_price` | `Float` | Precio de compra actual. |
| `sell_price` | `Float` | Precio de venta actual. |
| `amount` | `BigInteger` | Monto total transado en la jornada (en CLP). |
| `traded_units` | `BigInteger` | Número de unidades transadas. |
| `currency` | `String(10)` | Moneda de la transacción (ej. CLP). |
| `isin` | `String(50)` | Código ISIN del instrumento. |
| `green_bond` | `String(5)` | Indicador si es un bono verde. |

### `stock_closings`
Almacena los datos del cierre bursátil del día anterior.

| Columna | Tipo de Dato | Descripción |
| :--- | :--- | :--- |
| `date` | `Date` | **PK**. Fecha del cierre. |
| `nemo` | `String(20)` | **PK**. Código de la acción. |
| `previous_day_amount`| `Float` | Monto transado el día del cierre. |
| `previous_day_trades`| `Integer` | Número de negocios del día del cierre. |
| `previous_day_close_price` | `Float` | Precio al cierre. |
| `belongs_to_igpa` | `Boolean` | `True` si la acción pertenece al índice IGPA. |
| `belongs_to_ipsa` | `Boolean` | `True` si la acción pertenece al índice IPSA. |
| `weight_igpa` | `Float` | Ponderación de la acción en el IGPA. |
| `weight_ipsa` | `Float` | Ponderación de la acción en el IPSA. |
| `price_to_earnings_ratio` | `Float` | Razón Precio/Utilidad (PU). |
| `current_yield` | `Float` | Rentabilidad actual. |
| `previous_day_traded_units` | `BigInteger` | Unidades transadas el día del cierre. |

### `dividends`
Guarda la información sobre los dividendos anunciados.

| Columna | Tipo de Dato | Descripción |
| :--- | :--- | :--- |
| `id` | `Integer` | **PK**. Identificador único. |
| `nemo` | `String(20)` | Código de la acción. |
| `description` | `String(255)` | Descripción del dividendo. |
| `limit_date` | `Date` | Fecha límite para tener la acción y recibir el dividendo. |
| `payment_date`| `Date` | Fecha de pago del dividendo. |
| `currency` | `String(10)` | Moneda del dividendo. |
| `value` | `Float` | Valor del dividendo por acción. |
| `...` | `...` | Otras columnas con detalles contables (`num_acc_ant`, `pre_ex_vc`, etc.). |

### `anomalous_events`
Resultados del análisis de "drainer" para detectar eventos inusuales en el mercado.

| Columna | Tipo de Dato | Descripción |
| :--- | :--- | :--- |
| `id` | `Integer` | **PK**. Identificador único. |
| `nemo` | `String(20)` | Código de la acción asociada al evento. |
| `event_date` | `Date` | Fecha en que ocurrió el evento. |
| `event_type` | `String(50)` | Tipo de evento (ej. 'Pico de Volumen', 'Compra de Insider'). |
| `description`| `Text` | Descripción detallada del evento. |
| `source` | `String(100)`| Origen del dato (ej. 'Análisis Interno', 'Simulador CMF'). |
| `price_change_pct` | `Float` | Cambio porcentual del precio 5 días después del evento. |
| `analysis_timestamp` | `DateTime` | Fecha y hora en que se realizó el análisis. |

### `filtered_stock_history`
Almacena un historial de los cambios de precios *solo para las acciones que el usuario ha filtrado*.

| Columna | Tipo de Dato | Descripción |
| :--- | :--- | :--- |
| `id` | `Integer` | **PK**. Identificador único. |
| `timestamp` | `DateTime` | Fecha y hora del cambio. |
| `symbol` | `String(50)` | Código de la acción. |
| `price` | `Float` | Nuevo precio. |
| `previous_price` | `Float` | Precio anterior. |
| `price_difference` | `Float` | Diferencia absoluta entre precios. |
| `percent_change`| `Float` | Cambio porcentual. |

### Tablas de Configuración y Usuario

- **`users`**: Almacena usuarios de la aplicación (`id`, `username`, `email`).
- **`credentials`**: Guarda las credenciales de la Bolsa de Santiago para el login automático (`username`, `password`).
- **`stock_filters`**: Guarda los filtros de acciones seleccionados por el usuario (`codes_json`, `all`).
- **`column_preferences`**: Almacena las preferencias del usuario sobre qué columnas mostrar en la tabla principal.
- **`portfolio`**: Tabla para gestionar un portafolio de acciones (`symbol`, `quantity`, `purchase_price`).
- **`alerts`**: Guarda alertas de precios definidas por el usuario (`symbol`, `target_price`, `condition`).
- **`log_entries`**: Registro de eventos y errores de la aplicación.
- **`last_update`**: Tabla simple con un solo registro que indica el timestamp de la última actualización de datos.

### Tablas para Funcionalidades Futuras (IA)

- **`advanced_kpis`**: Almacenará KPIs avanzados generados por IA (`roe`, `beta`, `debt_to_equity`, `analyst_recommendation`, `source_details`, `calculation_details`).
- **`prompt_configs`**: Guardará la configuración para llamar a las APIs de IA (`api_provider`, `api_key`, `prompt_template`).

---

## 5. Filtros, Cálculos y Lógica de Negocio

### Filtros
El sistema aplica filtros en varios niveles:
1.  **Filtro de Visualización**: El usuario puede ingresar una lista de hasta 5 "Nemos" para ver solo esas acciones en la tabla principal. Esta configuración se guarda en la tabla `stock_filters`.
2.  **Filtro de Historial**: El sistema solo guarda registros en la tabla `filtered_stock_history` para las acciones que coinciden con el filtro del usuario. Esto se ejecuta solo durante el horario de mercado para evitar registrar cambios irrelevantes.
3.  **Filtro de Comparación**: La vista de comparación de históricos también utiliza este filtro para mostrar solo los cambios en las acciones de interés.

### Cálculos y Análisis

1.  **Comparación de Históricos (`db_io.py`)**:
    - La función `compare_last_two_db_entries` recupera los dos últimos snapshots de datos.
    - Compara el precio de cada acción entre ambos snapshots.
    - Calcula la **diferencia absoluta** (`new_price - old_price`) y la **diferencia porcentual** (`(diff / old_price) * 100`).
    - Clasifica las acciones en: `con cambios`, `sin cambios`, `nuevas` (aparecen en el último snapshot) y `eliminadas` (desaparecen).

2.  **Análisis de Picos de Volumen (`drainer_service.py`)**:
    - Utiliza la librería `pandas` para un análisis eficiente.
    - Carga 90 días de datos de la tabla `stock_closings`.
    - Para cada acción, calcula una **media móvil de 30 días** y la **desviación estándar** del volumen.
    - Un "pico" se define como un día donde el volumen supera `media + (3.5 * desviación estándar)`.
    - Para cada pico, calcula el impacto en el precio 5 días después.
    - Los resultados se guardan como `AnomalousEvent`.

3.  **Sincronización de Datos (Dividendos y Cierres)**:
    - **Dividendos**: Usa una estrategia de "reemplazo total". Borra la tabla y la vuelve a llenar con los datos frescos de la API. Esto asegura consistencia total.
    - **Cierres**: Usa una estrategia "upsert" (`INSERT ... ON CONFLICT DO UPDATE`). Esto es más eficiente, ya que solo inserta filas nuevas o actualiza las existentes para una fecha dada sin necesidad de borrar.

4.  **Servicio de IA (Simulado en `ai_financial_service.py`)**:
    - Actualmente, genera KPIs (ROE, Beta, etc.) con valores aleatorios.
    - La intención a futuro es usar los datos de la base para alimentar un *prompt* a un modelo de lenguaje (LLM) y obtener análisis financiero real. El sistema ya está preparado para almacenar estos prompts y sus resultados detallados.

---

Este documento provee una visión detallada y profunda de las funcionalidades, flujos de datos y lógica interna del proyecto. Si tienes más preguntas, no dudes en consultarme.