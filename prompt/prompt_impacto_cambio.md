# 📋 Prompt: Análisis de Impacto de Cambio

## Objetivo
Antes de modificar código crítico, evaluar sus efectos colaterales y planificar una refactorización segura.

---

## Prompt
> Estoy por modificar esta funcionalidad:
> ```
> {Ruta/función a modificar}
> ```
> Evalúa:
> - ¿Qué otras partes del sistema dependen de esta función?
> - ¿Qué pruebas deberían cubrir la modificación?
> - ¿Debo refactorizar algún módulo afectado?

### Resultado esperado:
- Reporte de impacto (lista de archivos y funciones afectadas)
- Sugerencia de orden de modificación
- Pruebas a ejecutar o crear antes/después
