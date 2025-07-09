
# Especificación Funcional del Sistema

## 1. Problema que Resuelve la Aplicación

La aplicación "Filtro de Acciones de la Bolsa de Santiago" está diseñada para **automatizar y simplificar el seguimiento de datos bursátiles** del mercado chileno. El principal problema que resuelve es la necesidad de monitorear de forma constante y centralizada un portafolio de acciones específico, eliminando la tarea manual y repetitiva de iniciar sesión en la plataforma de la Bolsa y consultar los valores uno por uno.

La herramienta ofrece una solución integral que abarca:
- **Captura automática de datos**: Mediante un bot de scraping que simula la interacción de un usuario.
- **Almacenamiento persistente**: Utilizando una base de datos optimizada para series temporales (TimescaleDB).
- **Visualización en tiempo real**: A través de una interfaz web que se actualiza automáticamente sin necesidad de recargar la página.

## 2. Usuarios del Sistema

Los usuarios de esta aplicación son **inversores, analistas financieros o cualquier persona con interés en el mercado de valores chileno** que necesite realizar un seguimiento activo de un conjunto de acciones.

El perfil de usuario requiere:
- Tener credenciales válidas (usuario y contraseña) para acceder al sitio web de la Bolsa de Santiago.
- Un conocimiento básico del mercado de acciones para interpretar los datos presentados (ej. códigos de acciones, precios de cierre, variaciones).

## 3. Casos de Uso Principales

A continuación, se describen las funcionalidades clave que la aplicación ofrece a sus usuarios.

### 3.1. Gestión de Credenciales
- **Caso de uso:** El usuario debe configurar sus credenciales de la Bolsa de Santiago para que el sistema pueda operar.
- **Flujo:**
    1. Al iniciar la aplicación por primera vez, el sistema redirige al usuario a una página de login.
    2. El usuario ingresa su nombre de usuario y contraseña.
    3. Opcionalmente, puede marcar "Recordar" para que las credenciales se almacenen de forma segura en la base de datos para futuros inicios de sesión.
    4. El sistema valida y guarda las credenciales.

### 3.2. Filtrado de Acciones
- **Caso de uso:** El usuario desea monitorear un conjunto específico de acciones.
- **Flujo:**
    1. En la pantalla principal, el usuario encuentra un campo para ingresar hasta 5 códigos de acciones (ej. "SQM-B", "CMPC").
    2. Tras ingresar los códigos, hace clic en el botón "Filtrar".
    3. El sistema guarda esta preferencia y la tabla de datos muestra únicamente la información de las acciones seleccionadas.
    4. El filtro se mantiene activo en sesiones futuras.

### 3.3. Visualización de Datos
- **Caso de uso:** El usuario necesita ver el estado actual de las acciones filtradas.
- **Flujo:**
    1. La tabla principal muestra los datos más recientes de las acciones, con columnas como código, precio, y variación.
    2. Los cambios de precio se resaltan con indicadores visuales (colores y flechas) para una rápida interpretación.
    3. El usuario puede personalizar qué columnas desea ver en la tabla.

### 3.4. Actualización de Datos
Existen dos modalidades para actualizar la información:

- **Actualización Manual:**
    - **Caso de uso:** El usuario quiere obtener los datos más recientes en un momento específico.
    - **Flujo:**
        1. El usuario hace clic en el botón "Actualizar".
        2. El sistema inicia en segundo plano el proceso de scraping para obtener nueva información.
        3. Al finalizar, la tabla en el frontend se actualiza automáticamente vía WebSockets.

- **Actualización Automática:**
    - **Caso de uso:** El usuario desea que la aplicación se mantenga actualizada sin intervención manual.
    - **Flujo:**
        1. El usuario selecciona un intervalo de tiempo desde un menú desplegable (ej. "Cada 5 minutos").
        2. El sistema programa una tarea que ejecutará el bot de scraping periódicamente.
        3. La tabla se actualiza automáticamente cada vez que se completan las actualizaciones programadas.

### 3.5. Consulta de Historial
- **Caso de uso:** El usuario necesita revisar la información de cargas de datos pasadas o comparar cambios.
- **Flujo:**
    1. El usuario navega a la sección "Histórico".
    2. Se muestra un resumen de las últimas ejecuciones del bot.
    3. Se presenta una comparación detallada entre los datos de las dos últimas actualizaciones, permitiendo identificar cambios específicos en los valores de las acciones. 