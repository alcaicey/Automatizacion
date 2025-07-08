
# Limitaciones y Problemas Conocidos

Este documento describe las limitaciones actuales de la arquitectura y la implementación de la aplicación. Identificar estos puntos es clave para priorizar futuros esfuerzos de refactorización y robustecimiento del sistema.

## 1. Fragilidad del Web Scraping

La dependencia de un sitio web externo es el principal punto de vulnerabilidad de la aplicación.

- **Dependencia de la Estructura del Sitio Web**: El bot se basa en selectores de CSS y en la estructura de las respuestas de la API del sitio de la Bolsa. Cualquier cambio en el frontend o backend del sitio (lo cual es común y puede ocurrir sin previo aviso) **romperá el bot** y la aplicación dejará de recibir datos.
- **Medidas Anti-Bot**: El sitio web objetivo utiliza mecanismos para detectar y bloquear la automatización (se ha observado tráfico relacionado con `Radware`, un proveedor de seguridad anti-bots). Esto puede resultar en bloqueos temporales o permanentes, CAPTCHAs, o cambios en el flujo de login que requieran una actualización constante del código del bot.
- **Gestión de Sesión Compleja**: Aunque el sistema intenta reutilizar las sesiones para ser más eficiente, las sesiones web pueden expirar de maneras inesperadas. Si la lógica de detección de sesión expirada falla, el bot puede entrar en un estado de error que requiera intervención manual (como borrar el archivo `playwright_state.json`).

## 2. Arquitectura Monolítica

La aplicación se ejecuta como un único proceso, lo que presenta desafíos de estabilidad y escalabilidad.

- **Falta de Aislamiento**: El bot de scraping se ejecuta en un hilo dentro del mismo proceso que el servidor web Flask. Un error no controlado y crítico en el hilo del bot (ej. un "crash" del navegador de Playwright o un consumo de memoria excesivo) tiene el potencial de **afectar o incluso detener por completo el servidor web**.
- **Dificultad para Escalar**: El modelo actual no permite escalar horizontalmente. No es posible ejecutar múltiples instancias de la aplicación para manejar más carga, ya que se producirían conflictos al intentar controlar la misma sesión del bot con las mismas credenciales. Cualquier aumento de carga debe ser manejado con escalado vertical (más CPU/RAM).

## 3. Gestión de Estado y Robustez

- **Punto Único de Fallo (Lock)**: Se utiliza un `asyncio.Lock` para asegurar que solo una instancia del bot se ejecute a la vez. Si por alguna razón el proceso del bot termina de forma abrupta sin liberar el lock, **ninguna actualización futura podrá iniciarse** hasta que la aplicación sea reiniciada por completo.
- **Persistencia de Estado Frágil**: El estado de la sesión de Playwright se guarda en un archivo (`playwright_state.json`). Si este archivo se corrompe, el bot podría ser incapaz de recuperar la sesión, requiriendo su eliminación manual para forzar un nuevo ciclo de login.

## 4. Seguridad de las Credenciales

- **Almacenamiento de Credenciales**: Las credenciales para el sitio de la Bolsa se almacenan en la base de datos en la tabla `credentials`. Basado en el código del modelo, parece que se guardan **en texto plano**. Esto representa un riesgo de seguridad significativo. Si la base de datos se viera comprometida, las credenciales del usuario quedarían expuestas. Se debería implementar un sistema de encriptación para estos datos sensibles.

## 5. Integridad de Datos

- **Mecanismo de Fallback a JSON**: El `README` menciona un sistema de fallback a archivos JSON si la base de datos no está disponible. Esta doble fuente de verdad puede llevar a **inconsistencias en los datos**, donde la información mostrada podría no reflejar el estado real de la base de datos una vez que esta vuelva a estar disponible. 