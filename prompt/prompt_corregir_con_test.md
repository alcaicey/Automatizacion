# 🧪 Prompt: Corrección Guiada con Test Previo

## Objetivo
Detectar errores, reproducirlos con pruebas y luego aplicar correcciones sin pérdida de funcionalidad.

---

## Prompt
> Se ha detectado este error:
> ```
> {Descripción del error o traceback}
> ```
> Analiza su causa.  
> Antes de corregir, genera un **test que reproduzca el error**.  
> Luego aplica el fix y ejecuta `pytest` para confirmar que:
> - 🟢 El error está resuelto
> - ✅ No se han roto otras funciones

### Recomendaciones:
- Usa mocks si dependes de APIs, WebSockets, DB externa o GUI automatizada.
- Revisa si ya hay test existente que debas actualizar.
