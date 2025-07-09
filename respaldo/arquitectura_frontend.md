# Arquitectura del Frontend

Este documento detalla la arquitectura modular del frontend de la aplicación, basada en clases de ES6, un orquestador central (`app.js`) y un sistema de inicialización de widgets basado en el DOM.

## Diagrama de Arquitectura y Flujo

El siguiente diagrama ilustra la relación entre los componentes principales y el flujo de inicialización.

```mermaid
graph TD
    subgraph "Inicialización"
        A[document.DOMContentLoaded] --> B(new App());
        B --> C{app.initializeApp()};
        C --> D[dashboardLayout.initializeLayout()];
    end

    subgraph "Orquestador Principal"
        E[app.js]
        E --> F[Socket.IO]
        E --> G[Managers]
        E --> H[EventHandlers]
        E --> I[DashboardLayout]
    end

    subgraph "Componentes Modulares"
        G --> M1[PortfolioManager];
        G --> M2[KpiManager];
        G --> M3[DividendManager];
        G --> M4[... otros managers];
        
        I --> W[Clona Widgets desde Plantillas HTML];
        W --> D_LAYOUT(Añade Widgets al DOM);
        D_LAYOUT --> K(Llama a manager.initializeWidget());
    end
    
    subgraph "Páginas Independientes (ej. Indicadores)"
        P_HTML[indicadores.html] --> P_JS[indicadores.js];
        P_JS --> P_MOCK(new MockApp());
        P_MOCK --> P_KPI[new KpiManager(mockApp)];
        P_MOCK --> P_DIV[new DividendManager(mockApp)];
        P_KPI --> P_INIT_KPI[kpiManager.initializeWidget()];
        P_DIV --> P_INIT_DIV[dividendManager.initializeWidget()];
    end

    classDef default fill:#282c34,stroke:#61afef,stroke-width:2px,color:#abb2bf;
    classDef important fill:#c678dd,stroke:#c678dd,color:#fff;
    class E,K,P_MOCK important;
```

## Flujo de Inicialización (Dashboard Principal)

1.  **`DOMContentLoaded`**: Cuando el DOM está listo, el script `app.js` (cargado como módulo al final del `body`) se ejecuta.
2.  **`new App()`**: Se crea la instancia principal de la aplicación.
    *   En su constructor, `App` instancia todos los managers (`PortfolioManager`, `KpiManager`, `UIManager`, etc.) y componentes de utilidad (`DashboardLayout`, `EventHandlers`).
    *   Crucialmente, pasa su propia instancia (`this`) al constructor de cada componente, proveyéndoles una referencia centralizada para acceder a otros managers o al estado de la aplicación.
3.  **`app.initializeApp()`**: Se llama a este método para continuar con la configuración.
4.  **`dashboardLayout.initializeLayout()`**: La responsabilidad de construir la interfaz de usuario se delega a `DashboardLayout`.
    *   Este componente lee la configuración de widgets (desde `localStorage` o una configuración por defecto).
    *   Para cada widget, clona su plantilla HTML (`<template>`) correspondiente.
    *   Añade el elemento clonado al DOM (dentro del grid de GridStack.js).
    *   **Paso Clave**: Una vez que el widget está en el DOM, `DashboardLayout` obtiene el manager correspondiente desde la instancia de `app` y llama a su método `manager.initializeWidget(widgetElement)`.

Este flujo asegura que el código de un manager (que busca elementos con `document.getElementById`) solo se ejecuta **después** de que su HTML correspondiente ha sido añadido a la página, evitando errores de "elemento no encontrado".

## Componentes Principales

*   **`app.js` (Clase `App`)**:
    *   **Rol**: Orquestador central.
    *   **Responsabilidades**:
        *   Contener el estado global de la aplicación (si es necesario).
        *   Instanciar y mantener referencias a todos los managers y utilidades.
        *   Proveer una API interna para que los componentes se comuniquen entre sí (ej. `this.app.uiManager.showFeedback(...)`).
        *   Gestionar la conexión principal de Socket.IO.

*   **`managers/*.js` (Clases `...Manager`)**:
    *   **Rol**: Módulos de lógica de negocio encapsulada.
    *   **Responsabilidades**:
        *   Gestionar la lógica específica de una sección (ej. Portafolio, KPIs).
        *   Manejar las llamadas a la API (`fetchData`) para sus datos.
        *   Implementar el método `initializeWidget()`, que se ejecuta cuando el widget es visible. Este método es responsable de cachear elementos del DOM y registrar event listeners específicos.
        *   Comunicarse con otros managers a través de la instancia `this.app`.

*   **`utils/dashboardLayout.js` (Clase `DashboardLayout`)**:
    *   **Rol**: Gestor de la interfaz de usuario del dashboard.
    *   **Responsabilidades**:
        *   Inicializar y gestionar la librería `GridStack.js`.
        *   Añadir, eliminar y reposicionar widgets en el grid.
        *   Orquestar la inicialización de los managers llamando a `initializeWidget()` en el momento adecuado.
        *   Guardar el estado del layout en `localStorage`.

*   **`utils/eventHandlers.js` (Clase `EventHandlers`)**:
    *   **Rol**: Registrador de eventos globales.
    *   **Responsabilidades**:
        *   Registrar listeners en elementos que no pertenecen a un widget específico (ej. botones en la barra de navegación, modales globales).
        *   Delegar acciones a los managers correspondientes (ej. un clic en "Guardar Preferencias de Portafolio" llama a `this.app.portfolioManager.savePreferences()`).

## Páginas Independientes (`indicadores.html`)

Algunas páginas como "Indicadores" no forman parte del dashboard principal y funcionan de manera aislada. Para mantener la consistencia:

*   Cargan sus scripts como módulos (`type="module"`).
*   Tienen un script de punto de entrada (ej. `pages/indicadores.js`).
*   Este script crea una **`MockApp`**, una clase simulada que provee las dependencias mínimas que los managers necesitan para funcionar fuera del dashboard (generalmente, una instancia de `UIManager` y la función `fetchData`).
*   Luego, instancia los managers que necesita (ej. `KpiManager`, `DividendManager`) y llama a sus métodos `initializeWidget()`.

Esta estrategia permite reutilizar los managers sin acoplarlos fuertemente al dashboard principal. 