# 🧪 Prompt: Diagnóstico de errores y generación de tests con `Agent Mode`

Este prompt está orientado a identificar errores en el sistema actual y generar **pruebas automatizadas** para evitar regresiones, siguiendo buenas prácticas para el stack Flask + SQLAlchemy + PyAutoGUI + Playwright.

---

## 🔎 Flujo sugerido

### 1. 📄 Revisión del error
- Lee la descripción del error (texto, logs, imágenes si están presentes)
- Determina en qué archivo/función ocurre
- Usa `read_file` y `problems` para reunir contexto

---

### 2. 🔧 Diagnóstico guiado
- Aplica análisis paso a paso del código implicado
- Si es necesario modificar algo, crear test antes de aplicar el fix
- NO eliminar funcionalidades existentes

---

### 3. 🧪 Generar test antes de corregir
- Ubicar carpeta `tests/`
- Generar prueba automatizada que **reproduzca el error**
- Usar `pytest`, `unittest.mock`, `MagicMock`, `pytest-mock`
- Usar mocks para sockets, UI, web o APIs externas

---

### 4. 🔁 Aplicar fix solo si el test está
- Realiza corrección
- Ejecuta `pytest` con `run_terminal_command`
- Validar que:
  - 🟢 El error se resuelva
  - ✅ No se rompa funcionalidad previa

---

### 5. 📈 Informe de cambios
- Usa `view_diff` para mostrar lo que cambió
- Entregar resumen:
  - Archivos modificados
  - Tests agregados
  - Validación exitosa
  - Pendientes abiertos

---

## 🛡️ Buenas prácticas
- Siempre probar antes y después de un cambio
- Usar mocks para flujos complejos
- NO modificar sin pruebas previas
