# 🧱 Prompt: Refactorización Responsable

## Objetivo
Mejorar el diseño y estructura del código sin cambiar su comportamiento funcional.

---

## Prompt
> Refactoriza el módulo `{nombre}` para:
> - Separar responsabilidades
> - Mejorar legibilidad y pruebas
> - Usar buenas prácticas del stack Flask + SQLAlchemy + servicios

### Indicaciones:
- **No cambies comportamiento observable**
- Ejecuta `pytest` al finalizar y muestra el resultado
- Usa `view_diff` para mostrar cambios clave
- Genera resumen: qué refactorizaste, por qué, y cómo se mantiene funcional
