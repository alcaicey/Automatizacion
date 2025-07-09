# Agentes de Automatización

Este proyecto implementa un sistema multi‑agente que automatiza la extracción y publicación de datos de acciones de la Bolsa de Santiago. A continuación se describe el propósito de cada agente, las entradas y salidas que maneja, los archivos que utiliza y cómo interactúan entre sí.

## 1. ScrapingAgent
**Archivo principal:** `src/scripts/bolsa_santiago_bot.py`

**Propósito**
- Automatizar el navegador (Playwright) para iniciar sesión y recuperar los precios de acciones.
- Generar una captura HAR de toda la sesión.
- Guardar un archivo JSON con los datos obtenidos y un resumen de la actividad.
- Mantener el estado de sesión para reutilizarlo en ejecuciones futuras.

**Entradas**
- Variables de entorno `BOLSA_USERNAME` y `BOLSA_PASSWORD`.
- Selectores CSS y patrones de URL definidos en `src/config.py`.
- Opcionalmente `BOLSA_NON_INTERACTIVE` para ejecutar sin intervención manual.

**Salidas**
- `logs_bolsa/acciones-precios-plus_<timestamp>.json`: datos de acciones.
- `logs_bolsa/network_capture.har`: captura HAR de la sesión.
- `logs_bolsa/network_summary_<timestamp>.json`: resumen generado por `HARParserAgent`.
- `logs_bolsa/bolsa_bot_log_<timestamp>.txt`: registro detallado de la ejecución.
- `logs_bolsa/playwright_state.json`: estado de autenticación (cookies, etc.).

**Interacción con otros agentes**
- Entrega el HAR a `HARParserAgent` para extraer la respuesta JSON.
- Es invocado por `ServiceAgent` para obtener datos nuevos.

**Depuración**
- Ejecutar `python -m src.scripts.bolsa_santiago_bot` para probar de forma aislada.
- Revisar `logs_bolsa/bolsa_bot_log_*.txt` y el HAR generado.
- Si la sesión expira, eliminar `playwright_state.json` para forzar un nuevo login.

## 2. HARParserAgent
**Archivo principal:** `src/scripts/har_analyzer.py`

**Propósito**
- Analizar el archivo HAR producido por el scraping.
- Ubicar las solicitudes relevantes a las APIs de la Bolsa y extraer la respuesta JSON.
- Detectar información de expiración de la sesión.
- Generar un resumen con las cabeceras y un avance de los datos encontrados.

**Entradas**
- Ruta al HAR (`logs_bolsa/network_capture.har`).
- Lista de patrones de URL principales y secundarias (desde `src/config.py`).

**Salidas**
- Archivo JSON con la respuesta completa de la API objetivo.
- Archivo de resumen con todas las solicitudes relevantes e información de sesión.

**Interacción con otros agentes**
- Es llamado por `ScrapingAgent` cuando termina la navegación.
- El resumen es leído por `SessionAgent` para conocer el tiempo restante de la sesión.

**Depuración**
- Ejecutar directamente `python -m src.scripts.har_analyzer <ruta.har>`.
- Habilitar nivel de log `DEBUG` para ver cada solicitud procesada.

## 3. ServiceAgent
**Archivo principal:** `src/scripts/bolsa_service.py`

**Propósito**
- Orquestar la ejecución periódica del scraping.
- Guardar los datos en la base de datos `StockPrice` y actualizar el registro `LastUpdate`.
- Emitir eventos WebSocket cuando llegan datos nuevos.
- Gestionar un hilo de actualización automática y evitar instancias duplicadas del bot.

**Entradas**
- Archivos JSON generados por `ScrapingAgent`.
- Parámetros de actualización (intervalos y opciones de ejecución).

**Salidas**
- Inserciones en la base de datos.
- Eventos `new_data` mediante Socket.IO para notificar al frontend.
- Registros en `logs_bolsa/bolsa_service.log`.

**Interacción con otros agentes**
- Llama a `ScrapingAgent` y espera a que genere el JSON/HAR.
- Usa `HARParserAgent` implícitamente cuando `ScrapingAgent` finaliza.
- Informa a `RealTimeSyncAgent` (Socket.IO) cada vez que se guardan datos nuevos.

**Depuración**
- Revisar `logs_bolsa/bolsa_service.log` para verificar el ciclo de ejecución.
- Utilizar la función `get_latest_data()` o `filter_stocks()` en un entorno interactivo.

## 4. SessionAgent
**Responsabilidad dispersa en:** `bolsa_santiago_bot.py` y `bolsa_service.py`

**Propósito**
- Mantener la sesión de Playwright activa reutilizando `playwright_state.json`.
- Detectar expiración mediante la información provista por `HARParserAgent` y relanzar el inicio de sesión cuando sea necesario.
- Cerrar sesiones anteriores en el sitio (funciones `MIS_CONEXIONES_TITLE_SELECTOR` y `CERRAR_TODAS_SESIONES_SELECTOR`).

**Entradas**
- Archivo de estado de sesión y datos de expiración.

**Salidas**
- Actualización del archivo `playwright_state.json`.
- Mensajes de log indicando tiempo restante o problemas de autenticación.

**Interacción con otros agentes**
- Depende del resumen generado por `HARParserAgent` para saber cuándo reiniciar la sesión.
- Trabaja codo a codo con `ScrapingAgent` para no repetir logins innecesarios.

**Depuración**
- Borrar `playwright_state.json` si las cookies están corruptas.
- Revisar en `logs_bolsa/network_summary_*.json` el campo `session_remaining_seconds`.

## 5. RealTimeSyncAgent
**Implementación principal:** uso de `Flask-SocketIO` en `src/extensions.py` y en `bolsa_service.py`

**Propósito**
- Mantener sincronizado el frontend con los datos más recientes.
- Enviar un evento `new_data` cada vez que `ServiceAgent` almacena precios nuevos.

**Entradas**
- Notificación de `ServiceAgent` cuando hay nueva información almacenada.

**Salidas**
- Evento WebSocket `new_data` al cliente.

**Interacción con otros agentes**
- Suscrito a los eventos de `ServiceAgent` (via `socketio.emit`).
- Sincroniza la interfaz web ubicada en `src/static/`.

**Depuración**
- Ejecutar la aplicación Flask (`python src/main.py`) y observar la consola del navegador para verificar la recepción del evento `new_data`.

---

## Flujo general de interacción
1. **ServiceAgent** programa o invoca manualmente a **ScrapingAgent**.
2. **ScrapingAgent** realiza la navegación automatizada, produce `*.har` y el JSON de acciones.
3. **HARParserAgent** analiza el HAR, extrae los datos JSON y detecta el tiempo de sesión restante.
4. **ServiceAgent** almacena los precios en la base de datos y notifica a **RealTimeSyncAgent**.
5. **RealTimeSyncAgent** envía el evento `new_data` al frontend, que actualiza la vista en tiempo real.
6. **SessionAgent** revisa la información de expiración para decidir si es necesario iniciar sesión nuevamente en la siguiente ejecución.

Este documento debería servir de referencia para nuevos desarrolladores que necesiten comprender la arquitectura de agentes y extender sus funcionalidades.
