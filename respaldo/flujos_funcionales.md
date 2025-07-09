
# Mapa de Flujos Funcionales

Este documento describe los flujos de usuario y procesos clave de la aplicación a través de diagramas de flujo.

## 1. Flujo de Primer Acceso e Inicio de Sesión

Este flujo describe lo que sucede cuando un usuario abre la aplicación por primera vez y necesita configurar sus credenciales.

```mermaid
graph TD
    subgraph "Navegador del Usuario"
        A(Abrir la aplicación) --> B{¿Credenciales en DB?}
    end

    subgraph "Backend"
        B -- No --> C[Redirigir a /login]
        B -- Sí --> E[Cargar Dashboard]
        G[Validar y guardar credenciales] -- "Éxito" --> E
        G -- "Error" --> H[Mostrar error en página de login]
    end
    
    subgraph "Navegador del Usuario"
        C --> D[Mostrar formulario de Login]
        D -- "Usuario ingresa datos y envía" --> F(Enviar credenciales a API)
        H --> D
    end
    
    subgraph "Backend"
       F --> G
    end
```

## 2. Flujo de Carga del Dashboard (Usuario ya autenticado)

Una vez que las credenciales están guardadas, este es el flujo de carga principal.

```mermaid
graph TD
    A[Usuario accede a la app] --> B[Backend sirve la página]
    B --> C[Frontend se inicializa]
    C --> D[Conectar al servidor WebSocket]
    D --> E[Solicitar datos iniciales vía API]
    E --> F{Backend consulta la DB}
    F --> G[Obtener última actualización de precios]
    G --> H[Obtener preferencias de filtros y columnas]
    H --> I[Backend envía datos a Frontend]
    I --> J[Frontend renderiza la tabla de acciones]
    J --> K[Listo para interacción]

    W[Servidor WebSocket] <-.-> D
    W -- "Nuevos datos disponibles" .-> J
```

## 3. Flujo de Actualización de Datos (Manual)

Este es el proceso que se desencadena cuando el usuario hace clic en "Actualizar".

```mermaid
graph TD
    subgraph "Frontend"
        A[Click en 'Actualizar'] --> B[Mostrar indicador de carga]
        A --> C(POST /api/stocks/update)
    end
    
    subgraph "Backend (Hilo Principal)"
        C --> D{¿Bot ya está corriendo?}
        D -- Sí --> E[Ignorar petición, responder 'ocupado']
        D -- No --> F[Responder 'proceso iniciado' (202 Accepted)]
        F --> G[Iniciar bot en nuevo Thread]
    end
    
    subgraph "Backend (Hilo del Bot)"
        G -- "asyncio.run_coroutine_threadsafe" --> H(Ejecutar run_bolsa_bot)
        H --> I{Realizar scraping}
        I -- Éxito --> J[Guardar datos en DB]
        J --> K[Emitir evento 'update_complete' por WebSocket]
        I -- Error --> L[Emitir evento 'bot_error' por WebSocket]
    end

    subgraph "Frontend"
        K --> M[Recibir evento y actualizar tabla]
        L --> N[Recibir evento y mostrar notificación de error]
        M --> O[Ocultar indicador de carga]
        N --> O
    end
```

## 4. Flujo de Filtrado de Acciones

Este flujo se activa cuando el usuario aplica un filtro en la tabla.

```mermaid
graph TD
    A[Usuario ingresa códigos de acciones] --> B[Click en 'Filtrar']
    B --> C[Enviar POST a /api/filters con los códigos]
    C --> D[Backend recibe y guarda los filtros en la DB]
    D --> E[Backend responde con 'Éxito']
    E --> F[Frontend solicita los datos actualizados con el nuevo filtro]
    F --> G[Backend consulta la DB usando los filtros guardados]
    G --> H[Backend devuelve los datos filtrados]
    H --> I[Frontend actualiza la tabla con los nuevos datos]
```

## 5. Flujo de Manejo de Errores y Reintentos del Bot

El bot de scraping está diseñado para ser resiliente. Este diagrama muestra su lógica interna de recuperación.

```mermaid
graph TD
    A(Inicio de `run_bolsa_bot`) --> B{Chequeo de sesión}
    B -- "Sesión OK" --> E[Intentar captura de datos]
    B -- "Sesión inválida" --> C[Re-Login automático]
    C -- "Login OK" --> E
    C -- "Login Falla" --> D[Abortar y emitir 'LoginError']

    E --> F{¿Captura exitosa?}
    F -- Sí --> G[Procesar y guardar datos]
    F -- No --> H{¿Reintentos < 3?}
    H -- Sí --> I[Esperar y reintentar captura]
    I --> E
    H -- No --> J[Abortar y emitir 'DataCaptureError']
``` 