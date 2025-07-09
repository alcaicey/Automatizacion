
# Roadmap Técnico y Backlog de Mejoras

Este documento presenta una lista de mejoras técnicas propuestas para la aplicación. Estas sugerencias están basadas en el análisis de la arquitectura actual y buscan mejorar la robustez, escalabilidad, seguridad y mantenibilidad del sistema a largo plazo.

## 1. Prioridad Alta: Desacoplar el Bot de Scraping

Esta es la mejora más impactante y fundamental para el futuro de la aplicación.

- **Problema:** La arquitectura monolítica actual, donde el bot de scraping se ejecuta en un hilo dentro del servidor web, es frágil, difícil de escalar y presenta riesgos de estabilidad.
- **Propuesta:**
    1.  **Migrar el bot a un microservicio independiente:** Crear una aplicación separada (ej. usando FastAPI o incluso un script puro de Python) cuya única responsabilidad sea el scraping.
    2.  **Introducir una cola de trabajos:** Utilizar un sistema como **Celery** con un broker (ej. **Redis** o **RabbitMQ**) para gestionar las tareas de scraping.
- **Flujo Propuesto:**
    1.  El servidor web principal (Flask), en lugar de ejecutar el bot directamente, publicaría un "trabajo de actualización" en la cola de Celery.
    2.  Uno o más "workers" del microservicio de scraping tomarían el trabajo de la cola y lo ejecutarían de forma aislada.
    3.  El resultado (éxito o error) podría ser comunicado de vuelta al servicio principal a través de la misma cola o actualizando el estado directamente en la base de datos.
- **Beneficios:**
    - **Aislamiento y Estabilidad:** Un fallo en el scraper ya no afectaría al servidor web.
    - **Escalabilidad Independiente:** Se podrían ejecutar múltiples workers de scraping en diferentes máquinas si la carga de trabajo aumenta.
    - **Mejor Gestión de Recursos:** Los recursos (CPU/RAM) para el scraping estarían separados de los del servicio web.

## 2. Prioridad Alta: Mejorar la Seguridad de las Credenciales

- **Problema:** Las credenciales de la Bolsa de Santiago se almacenan potencialmente en texto plano en la base de datos, lo cual es un riesgo de seguridad grave.
- **Propuesta:**
    1.  **Encriptar las contraseñas en la base de datos:** Antes de guardar una credencial, la contraseña debe ser encriptada.
    2.  **Utilizar una librería de criptografía estándar:** Emplear una librería robusta como `cryptography` en Python.
    3.  **Gestionar la clave de encriptación de forma segura:** La clave utilizada para encriptar y desencriptar las contraseñas debe ser tratada como un secreto y cargada desde una variable de entorno segura (o un servicio de gestión de secretos como AWS Secrets Manager), y **nunca** debe estar en el código fuente.
- **Beneficios:**
    - Reduce drásticamente el riesgo de exposición de credenciales si la base de datos es comprometida.

## 3. Prioridad Media: Refactorizar el Manejo de Datos

- **Problema:** La existencia de un posible fallback a archivos JSON introduce una complejidad innecesaria y un riesgo de inconsistencia de datos.
- **Propuesta:**
    1.  **Eliminar el fallback a JSON:** Convertir la base de datos en la **única fuente de verdad**. Si la base de datos no está disponible, la aplicación debería fallar de forma controlada en lugar de operar con datos potencialmente desactualizados.
    2.  **Asegurar transacciones atómicas:** Revisar todas las operaciones que involucran múltiples escrituras en la base de datos (ej. guardar precios y luego actualizar la tabla `last_update`) y asegurarse de que estén envueltas en una transacción de base de datos (`db.session.commit()`, `db.session.rollback()`).
- **Beneficios:**
    - Aumenta la fiabilidad e integridad de los datos.
    - Simplifica el código y el razonamiento sobre el estado del sistema.

## 4. Prioridad Media: Completar la Funcionalidad Multi-Usuario

- **Problema:** La base de datos ya incluye un modelo `User` y relaciones en `Alerts`, pero la aplicación opera principalmente con una configuración global.
- **Propuesta:**
    1.  **Implementar un sistema de autenticación propio:** Añadir registro, inicio de sesión y gestión de sesiones para los usuarios de la aplicación (se puede usar `Flask-Login`).
    2.  **Asociar todos los datos a un usuario:** Modificar los modelos como `Portfolio`, `StockFilter` y las tablas de preferencias para que tengan una clave foránea al `id` del usuario.
    3.  **Adaptar la lógica de negocio:** Asegurarse de que todas las consultas y operaciones se filtren por el `user_id` del usuario que ha iniciado sesión.
- **Beneficios:**
    - Permite que la aplicación sea utilizada por múltiples personas de forma segura y aislada.
    - Abre la puerta a nuevas funcionalidades personalizadas.

## 5. Prioridad Baja: Mejorar la Observabilidad del Bot

- **Problema:** Si el bot falla silenciosamente, puede ser difícil de diagnosticar.
- **Propuesta:**
    1.  **Crear un endpoint de "health check" para el bot:** Una ruta de API que no solo verifique si el proceso está corriendo, sino que realice una prueba rápida (ej. intentar alcanzar la página de login) para asegurar que la conectividad y la sesión son válidas.
    2.  **Mejorar el logging:** Estructurar los logs para que sean más fáciles de parsear y enviar a un sistema de monitoreo centralizado (ej. ELK Stack, Datadog).
- **Beneficios:**
    - Facilita la detección temprana y la depuración de problemas con el scraping. 