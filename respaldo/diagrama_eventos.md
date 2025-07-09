# Diagrama de Flujo de Eventos: Actualización de Datos del Dashboard

El siguiente diagrama de secuencia detalla el flujo real que ocurre cuando el usuario solicita una actualización de datos desde la interfaz principal.

```mermaid
sequenceDiagram
    actor Usuario
    participant Frontend
    participant "Backend (Flask)" as Backend
    participant "Subproceso (Thread)" as Thread
    participant DB

    Usuario->>+Frontend: 1. Hace clic en "Actualizar"
    Frontend->>+Backend: 2. POST /api/stocks/update
    
    Note right of Backend: Inicia un nuevo hilo para no bloquear al servidor.
    Backend->>+Thread: 3. start_scraping_thread()
    Backend-->>-Frontend: 4. Responde HTTP 200 (OK)<br/>"La actualización ha comenzado."

    Thread->>Thread: 5. Inicia el bot (Playwright) en un loop de asyncio.
    
    loop Proceso de Scraping
        Thread->>DB: 6. Guarda los nuevos datos extraídos.
    end

    Note right of Thread: Una vez finalizado el scraping...
    Thread->>Backend: 7. Emite evento 'update_completed' (vía Socket.IO)
    
    Backend->>-Frontend: 8. Re-transmite el evento 'update_completed' (vía WebSocket)
    
    Frontend->>+Frontend: 9. Recibe el evento y refresca la tabla.
    Usuario-->>-Frontend: 10. Ve los datos actualizados.
```
