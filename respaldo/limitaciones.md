
# Limitaciones y Problemas Conocidos

Este documento describe las limitaciones actuales de la arquitectura y la implementación de la aplicación. Identificar estos puntos es clave para priorizar futuros esfuerzos de refactorización y robustecimiento del sistema.

## 1. Fragilidad del Web Scraping

La dependencia de un sitio web externo es el principal punto de vulnerabilidad de la aplicación.

- **Dependencia de la Estructura del Sitio Web**: El bot se basa en selectores de CSS y en la estructura de las respuestas de la API del sitio de la Bolsa. Cualquier cambio en el frontend o backend del sitio (lo cual es común y puede ocurrir sin previo aviso) **romperá el bot** y la aplicación dejará de recibir datos.
- **Medidas Anti-Bot**: El sitio web objetivo utiliza mecanismos para detectar y bloquear la automatización (se ha observado tráfico relacionado con `Radware`, un proveedor de seguridad anti-bots). Esto puede resultar en bloqueos temporales o permanentes, CAPTCHAs, o cambios en el flujo de login que requieran una actualización constante del código del bot.
- **Gestión de Sesión Compleja**: Aunque el sistema intenta reutilizar las sesiones para ser más eficiente, las sesiones web pueden expirar de maneras inesperadas. Si la lógica de detección de sesión expirada falla, el bot puede entrar en un estado de error que requiera intervención manual.

## 2. Arquitectura y Escalabilidad

La arquitectura actual, basada en la delegación de tareas a procesos `Celery` worker, ha superado muchas de las limitaciones de un diseño monolítico tradicional. Sin embargo, persisten algunos desafíos.

- **Aislamiento de Procesos (Solucionado)**: El bot de scraping ahora se ejecuta en procesos `Celery` worker completamente separados del servidor web. Un fallo crítico en el bot ya no afectará la estabilidad del servidor Flask, mejorando significativamente la robustez general del sistema.
- **Escalabilidad Horizontal (Mejorada)**: El sistema ahora es escalable horizontalmente. Es posible añadir más `Celery workers` para procesar un mayor volumen de tareas de scraping en paralelo. El servidor web también puede escalarse, ya que la comunicación por WebSockets se gestiona de forma centralizada a través de `Redis`.
- **Gestión de Concurrencia (Mejorada)**: La gestión de tareas concurrentes ya no depende de un `Lock` local, sino del sistema de colas de `Redis` y la lógica de los `workers` de `Celery`, que es un mecanismo mucho más robusto y distribuido.

## 3. Gestión de Estado y Robustez

- **Dependencia de Redis**: La arquitectura actual depende críticamente de la disponibilidad del servidor Redis. Si Redis falla, se interrumpirá tanto la cola de tareas de Celery como la comunicación por WebSockets, paralizando las funcionalidades de actualización en tiempo real y en segundo plano.
- **Persistencia de Estado Frágil**: El estado de la sesión de Playwright se guarda en un archivo (`playwright_state.json`). Si este archivo se corrompe, el bot podría ser incapaz de recuperar la sesión, requiriendo su eliminación manual para forzar un nuevo ciclo de login.

## 4. Seguridad de las Credenciales

- **Almacenamiento de Credenciales**: Las credenciales para el sitio de la Bolsa se almacenan en la base de datos en la tabla `credentials`. Basado en el código del modelo, parece que se guardan **en texto plano**. Esto representa un riesgo de seguridad significativo. Si la base de datos se viera comprometida, las credenciales del usuario quedarían expuestas. Se debería implementar un sistema de encriptación para estos datos sensibles.

## 5. Integridad de Datos

- **Mecanismo de Fallback a JSON**: El `README` menciona un sistema de fallback a archivos JSON si la base de datos no está disponible. Esta doble fuente de verdad puede llevar a **inconsistencias en los datos**, donde la información mostrada podría no reflejar el estado real de la base de datos una vez que esta vuelva a estar disponible. 