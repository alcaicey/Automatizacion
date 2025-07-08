# Flujos principales de la aplicación

Los siguientes diagramas describen de forma simplificada cómo interactúa el usuario con la interfaz web.

## Carga inicial
```mermaid
flowchart TD
    A[Inicio] --> B[Revisar credenciales]
    B -->|Ok| C[Conectar WebSocket]
    C --> D[Leer filtros guardados]
    D --> E[Obtener última actualización]
    E --> F[Mostrar tabla de acciones]
```

## Al presionar **Filtrar**
```mermaid
flowchart TD
    A[Click Filtrar] --> B[Enviar códigos al servidor]
    B --> C[Servidor filtra datos]
    C --> D[Recibir respuesta]
    D --> E[Actualizar tabla]
```

## Al presionar **Actualizar**
```mermaid
flowchart TD
    A[Click Actualizar] --> B{¿Bot en ejecución?}
    B -- Sí --> C[Enviar ENTER al navegador]
    C --> D[Esperar datos nuevos]
    B -- No --> E[Lanzar bot]
    E --> D
    D --> F[Refrescar tabla]
```
