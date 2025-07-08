# Reglas de Negocio y Lógicas Específicas

Este documento complementa la `guia_reconstruccion.md` y detalla reglas de negocio, cálculos y lógicas de implementación específicas que no son evidentes en una revisión superficial de la arquitectura.

---

## 1. Reglas de la Lógica de Portafolio

### Regla 1.1: Doble Lógica de Cálculo del Portafolio (Backend y Frontend)

-   **Descripción**: El sistema contiene una duplicación de la lógica para calcular los valores del portafolio. Existe una versión en el backend que usa los precios de cierre, y otra en el frontend que usa los precios de mercado en tiempo real. Esto permite tener una vista "oficial" (al cierre) y una vista "en vivo".
-   **Ubicación de la Lógica**:
    -   **Backend**: `src/routes/api/portfolio_routes.py`, en el endpoint `/api/portfolio/view`.
    -   **Frontend**: `src/static/portfolioManager.js`, en la función `getDisplayData`.

-   **Implementación (Backend)**:
    1.  El endpoint `/api/portfolio/view` es llamado.
    2.  Consulta la tabla `Portfolio` para obtener los activos del usuario (`symbol`, `quantity`, `purchase_price`).
    3.  Para cada activo, realiza una subconsulta a la tabla `StockClosing` para obtener el último precio de cierre.
    4.  Calcula los valores (`current_value`, `gain_loss_total`, etc.) y devuelve un JSON con los datos pre-calculados.

-   **Implementación (Frontend)**:
    1.  El `portfolioManager.js` no usa el endpoint `/api/portfolio/view`. En su lugar, llama a `/api/portfolio` (que devuelve solo los activos crudos) y usa la lista de precios en tiempo real que ya tiene en memoria (obtenida a través de `socket.io` o del endpoint `/api/data`).
    2.  Para cada activo, el script realiza los siguientes cálculos en JavaScript:
        -   `Total Pagado` = `Cantidad` × `Precio de Compra`
        -   `Valor Actual` = `Cantidad` × `Precio de Mercado en Tiempo Real`
        -   `Ganancia/Pérdida ($)` = `Valor Actual` - `Total Pagado`
        -   `Ganancia/Pérdida (%)` = `(Ganancia/Pérdida ($) / Total Pagado) * 100`
-   **Motivo de la Duplicación**: Esta arquitectura permite que el sistema muestre una vista consolidada y calculada del portafolio al cargar la página (usando los datos de cierre del backend), pero también permite actualizar dinámicamente este portafolio en el frontend cada vez que llega un nuevo precio en tiempo real, sin necesidad de consultar al backend repetidamente.

#### Flujo de Datos (End-to-End) para la Vista en Tiempo Real:

1.  **Backend (Fuente de Datos)**: Se consultan dos tablas:
    -   `Portfolio`: Para obtener los activos del usuario.
    -   `StockPrice`: Para obtener los precios más recientes de todas las acciones.
2.  **Backend (API)**:
    -   El endpoint `GET /api/portfolio` devuelve la lista de activos.
    -   El endpoint `GET /api/data` devuelve la lista de precios actuales.
3.  **Frontend (Llamada)**:
    -   `portfolioManager.js` llama a `/api/portfolio` para obtener los activos al inicializarse.
    -   El `app.js` (o un manager de datos) llama a `/api/data` y recibe actualizaciones vía el evento de Socket.IO `new_data`.
4.  **Frontend (Lógica)**:
    -   `portfolioManager.js` en su función `getDisplayData` cruza los datos de los activos con el mapa de precios en tiempo real y ejecuta los cálculos matemáticos.
5.  **Frontend (Renderizado)**:
    -   Los datos calculados se pasan a la función `renderTable` de `uiManager.js`.
    -   Esta función utiliza la librería DataTables para dibujar o actualizar las filas de la tabla HTML con `id="portfolioTable"`.
    -   La función `renderSummary` de `portfolioManager.js` actualiza los totales en los elementos HTML con `id="totalPaid"`, `id="totalCurrentValue"`, etc.

---

## 2. Reglas de Ejecución y Programación del Bot

### Regla 2.1: Programación de Tareas con Intervalo Aleatorio (Frontend y Backend)

-   **Descripción**: Las actualizaciones automáticas se ejecutan en un intervalo de tiempo aleatorio dentro de un rango definido. Esta lógica está implementada de forma independiente tanto en el frontend (para sesiones de usuario activas) como en el backend (para actualizaciones en segundo plano).
-   **Ubicación**:
    -   **Frontend**: `src/static/autoUpdater.js`.
    -   **Backend**: `src/utils/scheduler.py`, funciones `start_periodic_updates` y `update_data_periodically`.
-   **Implementación**:
    -   **Frontend**: Cuando el usuario selecciona un intervalo, `autoUpdater.js` usa `Math.random()` para calcular un retardo y `setTimeout` para programar la próxima llamada a la función que refresca los datos.
    -   **Backend**: `scheduler.py` se inicia en un hilo separado desde `main.py`. La función `update_data_periodically` calcula un tiempo de espera con `random.uniform()` y luego duerme (`time.sleep()`) antes de ejecutar la siguiente captura de datos del bot.
-   **Motivo**: Simular un comportamiento menos robótico y más humano para evitar posibles detecciones, tanto en las peticiones iniciadas por el usuario como en las del servidor.

#### Flujo de Datos (End-to-End) para Actualización desde el Frontend:

1.  **Backend (Fuente de Datos)**: No aplica directamente a la programación, sino a la ejecución. Cuando se dispara, la fuente es la web de la Bolsa de Santiago.
2.  **Frontend (Lógica de Programación)**:
    -   `autoUpdater.js` calcula un tiempo aleatorio y usa `setTimeout`.
    -   Al cumplirse el tiempo, ejecuta `this.app.fetchAndDisplayStocks()`.
3.  **Frontend (Llamada a API)**:
    -   La función `fetchAndDisplayStocks()` en `dashboard.js` realiza una petición `GET` al endpoint `/api/data`.
4.  **Backend (Respuesta de API)**:
    -   El endpoint `/api/data` en `data_routes.py` llama a `get_latest_data()` de `db_io.py`. Esta función devuelve los datos más recientes de la tabla `StockPrice` o de un archivo JSON de respaldo. **No activa una nueva ejecución del bot**. Simplemente devuelve los datos más frescos que el scheduler del backend haya guardado.
5.  **Frontend (Renderizado)**:
    -   Los datos recibidos actualizan todas las tablas y componentes de la UI (portafolio, indicadores, etc.) a través de sus respectivos `managers`.

### Regla 2.2: Lógica de Refresco de Datos solo en Horario de Mercado

-   **Descripción**: La persistencia de datos históricos (`FilteredStockHistory`) y las actualizaciones automáticas (tanto en frontend como en backend) solo se activan dentro del horario de mercado de la Bolsa de Santiago (aprox. 09:30 - 16:00).
-   **Ubicación**:
    -   **Frontend**: `src/static/autoUpdater.js`, en la función `isTradingHours()`.
    -   **Backend**: `src/utils/db_io.py`, en la función `save_filtered_comparison_history`.
-   **Implementación**:
    -   **Frontend**: `autoUpdater.js` verifica `isTradingHours()` antes de programar una nueva actualización. Si está fuera de horario, detiene el temporizador.
    -   **Backend**: La función `save_filtered_comparison_history` comprueba la hora del `market_timestamp` antes de realizar la inserción en la base de datos.
-   **Motivo**: Evitar el almacenamiento de datos irrelevantes o estáticos y reducir la carga del sistema fuera del horario de transacciones.

#### Flujo de Datos (End-to-End) para Guardado Histórico:

1.  **Backend (Disparador)**: El `scheduler.py` (o una llamada manual) ejecuta el bot a través de `bolsa_service.py`.
2.  **Backend (Lógica)**: Dentro de `bolsa_service.py`, tras capturar y procesar los datos, se llama a `save_filtered_comparison_history()` en `db_io.py`.
3.  **Backend (Condición)**: Esta función extrae la hora de los datos recién capturados. Si no está en el rango `(9:30 <= hora < 16:00)`, la función retorna `None` y no hace nada.
4.  **Backend (Fuente de Datos)**: Si la condición se cumple, se realiza un `INSERT` en la tabla `FilteredStockHistory` de la base de datos.
5.  **Frontend**: No hay una representación directa de esta regla en el frontend, ya que es una decisión de persistencia en el backend. El usuario solo ve los datos históricos que sí fueron guardados cuando consulta la página de "Histórico".

### Regla 2.3: Estrategia de Refresco Alternativa (Legacy)

-   **Descripción**: El proyecto contiene una lógica (probablemente de una versión anterior) para actualizar los datos sin invocar todo el flujo de Playwright, intentando simplemente recargar una pestaña del navegador ya abierta.
-   **Ubicación**: `src/utils/scheduler.py`, función `send_enter_key_to_browser`.
-   **Implementación**:
    1.  Usa `psutil` para buscar un proceso de `Chromium` en ejecución.
    2.  Si lo encuentra, intenta usar `pygetwindow` para activar la ventana y enviar las teclas `CTRL+L` y `ENTER`.
    3.  Como último recurso, intenta enviar las mismas teclas "a ciegas" con `pyautogui`.
-   **Motivo**: Originalmente, podría haber sido una optimización para entornos interactivos donde un navegador se dejaba abierto, evitando el coste de iniciar Playwright cada vez.

---

## 3. Reglas de Análisis de Datos

### Regla 3.1: Fórmula para Detección de Picos de Volumen

-   **Descripción**: El sistema tiene una regla estadística precisa para identificar un "pico de volumen anómalo".
-   **Ubicación**: `src/scripts/drainer_service.py`, función `_analyze_volume_spikes`.
-   **Implementación**:
    1.  Se cargan los datos de cierre de los últimos **90 días**.
    2.  Para cada acción, se calcula la **media móvil de 30 días** (`volume_ma`) y la **desviación estándar de 30 días** (`volume_std`) del volumen transado.
    3.  Se considera un "pico" si el volumen de un día (`previous_day_amount`) es mayor que `volume_ma + (volume_std * 3.5)`.
    4.  Adicionalmente, se calcula el cambio de precio **5 días después** del pico para medir su impacto.
-   **Motivo**: Implementar una detección de anomalías objetiva y basada en principios estadísticos, en lugar de umbrales fijos.

#### Flujo de Datos (End-to-End):

1.  **Disparador (Frontend)**: El usuario hace clic en un botón (ej. `id="runAnalysisBtn"`). Esto invoca la función `runAnalysis()` en `src/static/drainerManager.js`.
2.  **Llamada a API (Inicio)**: El script realiza una petición `POST` al endpoint `/api/drainers/analyze`.
3.  **Procesamiento Asíncrono (Backend)**:
    -   El endpoint en `drainer_routes.py` recibe la petición.
    -   Inicia la función `run_drainer_analysis()` de `drainer_service.py` en un **hilo de ejecución separado** y responde inmediatamente al cliente con un estado `202 Accepted`.
    -   La función de servicio consulta la tabla `StockClosing` para obtener el historial de precios y volúmenes de los últimos 90 días.
    -   Aplica la lógica estadística (media móvil, desviación estándar) para identificar los picos.
4.  **Almacenamiento de Resultados (Backend)**: Para cada pico de volumen detectado, se inserta una nueva fila en la tabla `AnomalousEvent`.
5.  **Notificación de Finalización (Backend -> Frontend)**: Una vez que el hilo de análisis termina, el servidor emite un evento de `Socket.IO` llamado `drainer_complete`.
6.  **Petición de Datos (Frontend)**: Al recibir el evento `drainer_complete`, `drainerManager.js` invoca a su función `fetchEvents()`.
7.  **Llamada a API (Obtención)**: La función `fetchEvents()` realiza una petición `GET` al endpoint `/api/drainers/events`.
8.  **Respuesta de API (Backend)**: El endpoint consulta todas las filas de la tabla `AnomalousEvent` y las devuelve como un JSON.
9.  **Renderizado (Frontend)**: El `drainerManager.js` recibe la lista de eventos y usa la librería DataTables para poblar la tabla HTML (`id="drainersTable"`), mostrando los resultados al usuario.

---

## 4. Reglas de Gestión de Datos y Resiliencia

### Regla 4.1: Persistencia Dual (Base de Datos y JSON)

-   **Descripción**: El sistema no depende exclusivamente de la base de datos. Utiliza archivos JSON como un mecanismo de respaldo (fallback) y como caché.
-   **Ubicación**: `src/utils/scheduler.py` y `src/utils/db_io.py`.
-   **Implementación**:
    -   **Escritura**: El bot guarda los resultados crudos de cada captura en un archivo `acciones-precios-plus_YYYYMMDD_HHMMSS.json`.
    -   **Lectura Fallback**: La función `get_latest_data` en `db_io.py`, si no puede obtener datos de la base de datos, intenta leer el último archivo JSON disponible del disco.
    -   **Caché con Hash**: Una lógica en `scheduler.py` calcula el hash MD5 de los archivos JSON para detectar si los datos han cambiado desde la última captura, evitando así escrituras redundantes en la base de datos si el contenido es idéntico.
-   **Motivo**: Aumentar la resiliencia de la aplicación (puede mostrar datos incluso si la DB está caída) y optimizar el rendimiento al evitar operaciones innecesarias.

#### Flujo de Datos (End-to-End) para Resiliencia:

1.  **Disparador (Frontend)**: El usuario carga una página que necesita datos de mercado, como el Dashboard. Se invoca una función como `fetchAndDisplayStocks()` en `dashboard.js`.
2.  **Llamada a API (Frontend)**: El script realiza una petición `GET` al endpoint `/api/stocks` (a menudo referido como `/api/data`).
3.  **Lógica de Obtención de Datos (Backend)**:
    -   El endpoint en `data_routes.py` recibe la petición y llama a la función `get_latest_data()` de `src/utils/db_io.py`.
    -   **Intento 1 (Base de Datos)**: La función `get_latest_data()` primero intenta conectarse a la base de datos y consultar la tabla `StockPrice` para obtener los datos más recientes.
    -   **Intento 2 (Fallback a JSON)**: Si la consulta a la base de datos falla (por ejemplo, si la DB está desconectada o la tabla está vacía), el bloque `except` se activa. Dentro de este bloque, la función busca en el directorio de `logs` el último archivo `acciones-precios-plus_*.json`, lo lee y carga su contenido.
4.  **Respuesta de API (Backend)**: El endpoint devuelve al frontend el conjunto de datos que haya logrado obtener, ya sea desde la base de datos o desde el archivo JSON de respaldo.
5.  **Renderizado (Frontend)**: El frontend recibe el JSON de datos y no es consciente de su origen. Procede a renderizar las tablas y gráficos como lo haría normalmente. El efecto visible para el usuario es que **la aplicación sigue mostrando datos, aunque sean ligeramente antiguos, en lugar de un error catastrófico**.

### Regla 4.2: Coloreado Condicional de Datos en la UI

-   **Descripción**: En la interfaz de usuario, los números que representan ganancias, pérdidas o variaciones se colorean de verde si son positivos y de rojo si son negativos.
-   **Ubicación**: `src/static/uiManager.js` (lógica de formato) y `portfolioManager.js` (aplicación de la lógica).
-   **Implementación**:
    -   `uiManager.js` tiene una función `createNumberRenderer` que puede generar HTML con clases de CSS (`text-success` o `text-danger`) según el signo del número.
    -   Otros managers, como `portfolioManager.js`, usan esta función para aplicar el formato a las columnas de sus tablas antes de renderizarlas con DataTables.
-   **Motivo**: Mejorar la legibilidad y la experiencia del usuario, permitiendo una rápida identificación visual de valores positivos y negativos.

#### Flujo de Datos (End-to-End):

1.  **Backend (Fuente de Datos)**: No aplica directamente, la regla es de formato.
2.  **Backend (API)**: No aplica.
3.  **Frontend (Llamada)**: La lógica se aplica sobre datos ya existentes en el cliente.
4.  **Frontend (Lógica)**:
    -   `uiManager.js` contiene la función `createNumberRenderer(isPercent)`.
    -   Esta función devuelve otra función (un *closure*) que toma un valor numérico como entrada.
    -   Dentro de esta, se comprueba si `data >= 0`. Si es así, se formatea el número y se envuelve en un `<span>` con la clase CSS `text-success`. Si no, se usa la clase `text-danger`.
5.  **Frontend (Renderizado)**:
    -   Al configurar la tabla con DataTables en `portfolioManager.js` (y otros), se asigna este renderer a las columnas deseadas.
    -   Por ejemplo: ` { data: 'gain_loss_percent', render: this.app.uiManager.createNumberRenderer(true) }`.
    -   DataTables ejecuta esta función de renderizado para cada celda de la columna, generando el HTML con el color correspondiente que se inyecta en el `<td>` de la tabla. 