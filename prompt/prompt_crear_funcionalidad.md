# ⚙️ Prompt: Crear Nueva Funcionalidad (Agent Mode)

## Objetivo
Diseñar e implementar una nueva funcionalidad basada en un requerimiento funcional específico, asegurando pruebas y compatibilidad con el sistema actual.

---

## Prompt
> Crea una nueva funcionalidad llamada `{Nombre}`.  
> Basada en este requerimiento funcional:
> ```
> {Descripción funcional}
> ```
> Usa el stack actual del proyecto: **Flask + SQLAlchemy + Blueprints + JS (si aplica)**.

### Instrucciones específicas:
- Genera el módulo correspondiente (modelo, servicio, route).
- Añade pruebas unitarias e integración en `/tests`.
- Actualiza el archivo de rutas, el modelo y el esquema si es necesario.
- Ejecuta `pytest` y muéstrame el resultado.
- Reporta si hay impactos en funcionalidades existentes y sugiere regresiones a probar.
