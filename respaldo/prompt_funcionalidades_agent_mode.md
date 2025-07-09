# 🧠 Prompt: Completa funcionalidades según documentación (`Agent Mode` activado)

Este prompt está diseñado para usarse con [Continue](https://docs.continue.dev/) en modo **Agent**, permitiendo acceso automático a herramientas como `create_new_file`, `read_file`, `run_terminal_command`, y `view_diff`.

---

## 🔧 Objetivo

Comparar `documentacion_detallada.md` con el código actual del proyecto y **generar todas las funcionalidades faltantes**, integrarlas y validarlas mediante pruebas automatizadas.

---

## 🔁 Flujo completo

### 1. 📖 Comparación de documentación vs código
- Leer `documentacion_detallada.md`
- Revisar estructura actual (`src/`, `routes/`, `templates/`, `static/`)
- Identificar funcionalidades faltantes
- Entregar listado organizado al usuario

---

### 2. 🏗 Generación de funcionalidades
- Crear nuevos módulos con `create_new_file`
- Integrar en rutas existentes (`main.py`, blueprints, scripts)
- Actualizar frontend (HTML/JS) si es necesario
- Usar mocks para simular APIs externas o automatización gráfica (Playwright, PyAutoGUI)

---

### 3. ✅ Pruebas automáticas
- Crear test unitarios y de integración
- Librerías: `pytest`, `pytest-flask`, `pytest-playwright`, `unittest.mock`
- Añadir pruebas de regresión para lo que se modifique

---

### 4. 🧪 Ejecutar tests
- Usar `run_terminal_command` con `pytest`
- Refactorizar si hay fallos

---

### 5. 🧾 Revisión de cambios
- Ejecutar `view_diff` para confirmar cambios
- Generar resumen con:
  - Funcionalidades agregadas
  - Tests implementados
  - Pendientes o dudas abiertas

---

### 6. 📈 Reporte por etapas
- Informa el avance tras cada paso:
  - “🔍 Paso 1 completado: X funcionalidades faltantes encontradas.”
  - “🧠 Paso 2 completado: Módulo Y creado.”
  - “🧪 Paso 4 completado: Todos los tests pasaron.”

---

## ⚠️ Reglas críticas
- NO borrar lógica actual funcional
- Usar mocks si hay dependencias externas
- Parar y pedir aclaraciones si hay ambigüedad

