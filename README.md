# Documentación de la Aplicación de Filtro de Acciones

## Descripción General

Esta aplicación web permite filtrar y visualizar datos de acciones de la Bolsa de Santiago en tiempo real. La aplicación utiliza un script de scraping existente para obtener los datos más recientes, y proporciona una interfaz intuitiva para filtrar y visualizar la información.

## Características Principales

1. **Interfaz de Usuario Responsiva**:
   - Diseño adaptable para dispositivos móviles y escritorio
   - Campos para ingresar hasta 5 códigos de acciones
   - Tabla de resultados con indicadores visuales

2. **Filtrado de Acciones**:
   - Búsqueda por códigos de acciones (nemos)
   - Persistencia de búsquedas anteriores
   - Botones para filtrar y limpiar campos

3. **Actualización de Datos**:
   - Actualización manual mediante botón (ejecuta directamente bolsa_santiago_bot.py)
   - Indicador de progreso durante la generación del JSON (hasta 20 segundos)
   - Actualización automática configurable (1-3 o 1-5 minutos)
   - Indicador de próxima actualización y timestamp del último archivo JSON
   - Actualización en tiempo real vía WebSocket al almacenar nuevos datos

4. **Visualización de Datos**:
   - Tabla con columnas para Acción, Precio, Variación, Compra, Venta, Monto, Moneda y Volumen
   - Indicadores visuales (flechas y colores) para variaciones positivas y negativas
   - Animación de actualización para cambios en los datos

## Estructura del Proyecto

```
bolsa_app/
├── venv/                  # Entorno virtual de Python
├── src/
│   ├── models/            # Modelos de datos (no utilizados en esta versión)
│   ├── routes/            # Rutas de la API
│   │   ├── api.py         # Endpoints de acciones
│   │   └── user.py        # Endpoints de usuarios
│   ├── scripts/           # Scripts de servicio
│   │   ├── __init__.py
│   │   └── bolsa_service.py  # Servicio para gestionar datos de acciones
│   ├── static/            # Archivos estáticos
│   │   ├── index.html     # Página principal
│   │   ├── styles.css     # Estilos CSS
│   │   └── app.js         # Lógica de frontend
│   └── main.py            # Punto de entrada de la aplicación
└── requirements.txt       # Dependencias de Python
```

## Configuración Personalizada

Esta aplicación utiliza un archivo de configuración (`src/config.py`) donde se definen las rutas por defecto y otros parámetros estáticos. Las variables de entorno `BOLSA_SCRIPTS_DIR` y `BOLSA_LOGS_DIR` son opcionales y permiten sobrescribir dichas rutas:

- **Scripts de scraping**: `<BOLSA_SCRIPTS_DIR>/bolsa_santiago_bot.py`
- **Archivos JSON generados**: `<BOLSA_LOGS_DIR>/acciones-precios-plus_*.json`

La aplicación siempre selecciona el archivo JSON más reciente basándose en la fecha de modificación y muestra el timestamp extraído del nombre del archivo en la interfaz.

## Estructura del JSON

La aplicación está configurada para trabajar con la estructura específica del JSON generado por el script:

```json
{
  "listaResult": [
    {
      "NEMO": "AAISA",
      "PRECIO_CIERRE": 220,
      "VARIACION": 0.18,
      "PRECIO_COMPRA": 220,
      "PRECIO_VENTA": 221,
      "MONTO": 2203979,
      "MONEDA": "CLP",
      "UN_TRANSADAS": 10041
    },
    ...
  ]
}
```

La aplicación normaliza automáticamente los nombres de los campos para mantener la consistencia en la interfaz de usuario.

## Requisitos

- Python 3.11 o superior
- Navegador web moderno (Chrome, Firefox, Edge, Safari)
- Conexión a Internet
- Scripts `bolsa_santiago_bot.py` y `har_analyzer.py` ubicados en `src/scripts`

## Variables de Entorno

Antes de ejecutar la aplicación se deben definir las siguientes variables de entorno:

- **BOLSA_USERNAME** y **BOLSA_PASSWORD**: credenciales para iniciar sesión en el sitio de la Bolsa de Santiago. Estas credenciales **deben** establecerse como variables de entorno; si no están definidas el bot abortará su ejecución. En `src/config.py` las variables correspondientes tienen un valor vacío por defecto.
- **BOLSA_SCRIPTS_DIR**: (opcional) ruta al directorio que contiene `bolsa_santiago_bot.py`. Por defecto apunta a la carpeta `src/scripts` del proyecto.
- **BOLSA_LOGS_DIR**: (opcional) directorio donde el bot almacenará sus logs y archivos JSON. Si no se especifica se utiliza `logs_bolsa` dentro de la carpeta `src` del proyecto.
- **DATABASE_URL**: cadena de conexión para PostgreSQL/TimescaleDB. Ejemplo: `postgresql://postgres:postgres@localhost:5432/bolsa`.
- **BOLSA_NON_INTERACTIVE**: si se establece en `1`, permite ejecutar `bolsa_santiago_bot.py` sin confirmación de usuario. Útil para automatización y pruebas.
  Para ejecutar el bot de forma interactiva (por ejemplo si se presenta un CAPTCHA),
  omite esta variable o envía `{"non_interactive": false}` al endpoint `/api/stocks/update`.
  Si el parámetro `non_interactive` no se especifica en el endpoint, se empleará
  el valor actual de `BOLSA_NON_INTERACTIVE`. Si la variable no está definida, al
  iniciar la aplicación con `python src/main.py` se preguntará si se desea habilitar
  la ejecución no interactiva.

## Instalación y Ejecución

1. **Preparación del entorno**:
   ```bash
   # Descomprimir el archivo o clonar el repositorio
   # Ubicarse en la raíz del proyecto (donde se encuentra este README)
   
   # Crear y activar entorno virtual
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   
    # Instalar dependencias (incluye pytest)
    pip install -r requirements.txt
    # Instalar dependencias de sistema para Playwright
    npx playwright install-deps
    # Instalar los navegadores de Playwright
   python -m playwright install
   # Iniciar TimescaleDB con docker-compose

   docker-compose up -d db
   ```

### Instalación paso a paso en PowerShell

Al usar PowerShell 5.x no está disponible el operador `&&`. Ejecuta cada comando por separado:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt  # incluye pytest
npx playwright install-deps
python -m playwright install
docker-compose up -d db
```

2. **Ejecución de la aplicación**:
   ```bash
   # Desde la raíz del proyecto donde se configuró el entorno virtual
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   
   python src/main.py
   ```

3. **Acceso a la aplicación**:
   - Abrir un navegador web
   - Acceder a `http://localhost:5000`

## Uso de la Aplicación

1. **Filtrar Acciones**:
   - Ingresar hasta 5 códigos de acciones en los campos de texto
   - Hacer clic en "Filtrar" para mostrar los resultados
   - Los códigos se guardan automáticamente para futuras sesiones

2. **Actualización de Datos**:
   - Hacer clic en "Actualizar" para ejecutar el script bolsa_santiago_bot.py y obtener datos recientes
   - Durante la actualización se muestra un indicador de progreso (puede tardar hasta 20 segundos)
   - Si es necesario resolver un CAPTCHA manualmente, realiza la petición POST a `/api/stocks/update` enviando `{"non_interactive": false}` para ejecutar el bot de forma interactiva. Si no se incluye este campo, se tomará el valor configurado en `BOLSA_NON_INTERACTIVE`.
   - Seleccionar un modo de actualización automática en el desplegable:
     - Desactivado: Sin actualización automática
     - Random 1-3 minutos: Actualización aleatoria entre 1 y 3 minutos
     - Random 1-5 minutos: Actualización aleatoria entre 1 y 5 minutos

3. **Visualización de Resultados**:
   - La tabla muestra los datos de las acciones filtradas
   - Las variaciones positivas se muestran en verde con flecha hacia arriba
   - Las variaciones negativas se muestran en rojo con flecha hacia abajo
   - El timestamp de la última actualización se muestra en la parte superior de la tabla

## Notas Técnicas

- La aplicación utiliza Flask como backend y JavaScript puro para el frontend
- El scraping se realiza mediante el script bolsa_santiago_bot.py existente
- Los datos se leen directamente desde los archivos JSON generados en la ubicación especificada
- La actualización automática se gestiona tanto en el servidor como en el cliente
- Los datos se almacenan en PostgreSQL/TimescaleDB y se notifican mediante SocketIO
- El cliente web carga la librería de Socket.IO desde un CDN (`https://cdn.socket.io`)
- La aplicación detecta automáticamente la estructura del JSON y normaliza los campos
- El analizador HAR también revisa la respuesta de `getEstadoSesionUsuario` y, si contiene fecha o duración de expiración, calcula el tiempo restante de la sesión.

## API de Usuarios

Los endpoints para gestionar usuarios se encuentran bajo la ruta `/api/users`.
Las operaciones disponibles incluyen:

- `GET /api/users` para obtener todos los usuarios.
- `POST /api/users` para crear un usuario nuevo.
- `GET /api/users/<id>` para consultar un usuario por su identificador.
- `PUT /api/users/<id>` para actualizarlo.
- `DELETE /api/users/<id>` para eliminarlo.

## Solución de Problemas

- **Error de acceso a archivos**: Verificar que las rutas configuradas en bolsa_service.py sean correctas
- **Datos no actualizados**: Hacer clic en "Actualizar" para ejecutar manualmente el script de scraping
- **Errores de scraping**: Revisar los logs generados por el script bolsa_santiago_bot.py

## Personalización Adicional

Si necesitas usar rutas diferentes a las predeterminadas puedes definir las
variables de entorno `BOLSA_SCRIPTS_DIR` y `BOLSA_LOGS_DIR` antes de ejecutar la
aplicación. De esta forma no es necesario modificar `src/config.py`.

## Futuras Mejoras

- **Persistencia en la nube con TimescaleDB**: Los precios que actualmente se
  almacenan únicamente en archivos JSON también se guardarán en una base de datos
  TimescaleDB (sobre PostgreSQL). Esta solución está optimizada para series de
  tiempo y permitirá consultas históricas y análisis más avanzados.
- **Actualización en tiempo real de la interfaz**: Se incorporará un servidor
  WebSocket (por ejemplo mediante Flask‑SocketIO) para notificar a los clientes
  cada vez que nuevos registros se inserten en la base de datos. Así, la tabla se
  actualizará inmediatamente sin necesidad de recargar la página.
- **Refactorización del servicio**: `bolsa_service.py` y `bolsa_santiago_bot.py`
  se modificarán para escribir de forma simultánea en JSON y en TimescaleDB.
    También se prepararán scripts de despliegue (por ejemplo `docker-compose`) para
    facilitar el uso de TimescaleDB en entornos cloud.

## Ejecución de Pruebas

Para ejecutar las pruebas automatizadas de la aplicación (todas las dependencias se instalan desde `requirements.txt`, incluido `pytest`):

```bash
pip install -r requirements.txt
npx playwright install-deps
python -m playwright install
pytest -q
```

Al establecer `BOLSA_NON_INTERACTIVE=1` las pruebas podrán ejecutar el bot de forma
no interactiva. De manera equivalente, puede invocar `/api/stocks/update` con
`{"non_interactive": true}`.

Para comprobar que la base de datos configurada es accesible se puede ejecutar
el siguiente comando después de completar la instalación:

```bash
pytest tests/test_database_connection.py
```

