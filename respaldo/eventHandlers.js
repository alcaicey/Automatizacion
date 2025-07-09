// src/static/js/utils/eventHandlers.js

import KpiManager from '../managers/kpiManager.js';

export default class EventHandlers {
    constructor(app) {
        if (!app) {
            throw new Error('EventHandlers requiere una instancia de la aplicación (app).');
        }
        this.app = app;
        this.uiManager = app.uiManager;
    }

    initialize() {
        console.log('[EventHandlers] Adjuntando listeners de eventos principales...');
        
        // Clic en el botón de "Actualizar Ahora"
        // --- INICIO DE LA MODIFICACIÓN: Deshabilitado para evitar duplicidad de eventos ---
        // const updateNowBtn = document.getElementById('update-now-btn');
        // if (updateNowBtn) {
        //     updateNowBtn.addEventListener('click', () => this.handleUpdateClick());
        // }
        // --- FIN DE LA MODIFICACIÓN ---

        // Clic en el botón para cambiar el tema (oscuro/claro)
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.handleThemeToggle());
        }

        // --- MANEJADOR CENTRAL DE EVENTOS DE WIDGETS ---
        document.addEventListener('widgetAdded', (e) => {
            const { widgetId, element } = e.detail;
            const manager = this.app.getWidgetManager(widgetId);
            if (manager && typeof manager.initializeWidget === 'function') {
                console.log(`[Event] Inicializando widget: '${widgetId}'...`);
                manager.initializeWidget(element);
            } else {
                console.log(`[Event] El widget '${widgetId}' fue añadido, pero no tiene un manager o método initializeWidget.`);
            }
        });
        
        // Manejar clics en la lista de widgets para añadir uno nuevo
        const widgetList = document.getElementById('widget-list');
        if (widgetList) {
            widgetList.addEventListener('click', (e) => {
                e.preventDefault();
                const widgetId = e.target.dataset.widgetId;
                if (widgetId && this.app.dashboardLayout) {
                    this.app.dashboardLayout.addWidget(widgetId);
                }
            });
        }
    }

    // Maneja el clic en el botón de actualización principal
    handleUpdateClick() {
        console.log('[EventHandlers] Se solicitó una actualización manual.');
        
        // --- INICIO DE LA CORRECCIÓN ---
        // Se utiliza el nuevo método getState() para una comprobación de estado explícita.
        if (!this.app.botStatusManager) {
            console.error('[EventHandlers] Error: botStatusManager no está definido en la app.');
            this.uiManager.showFeedback('error', 'El componente de estado del bot no está disponible.');
            return;
        }

        const state = this.app.botStatusManager.getState();
        if (state.isUpdating) {
            console.warn('[EventHandlers] Se intentó actualizar mientras ya había una actualización en curso.');
            this.uiManager.showFeedback('info', 'El proceso de actualización ya está en marcha.');
            return;
        }
        
        this.uiManager.showFeedback('info', 'Iniciando actualización manual...');
        this.app.botStatusManager.setUpdating(true, 'Iniciando actualización...');
        
        // Llamar al endpoint de la API REST para iniciar la actualización
        this.app.fetchData('/api/stocks/update', { method: 'POST' })
            .catch(error => {
                console.error('[EventHandlers] Error al llamar a la API de actualización:', error);
                this.uiManager.showFeedback('danger', 'No se pudo iniciar la actualización.');
                this.app.botStatusManager.setUpdating(false, 'Error al iniciar.');
            });
        // --- FIN DE LA CORRECCIÓN ---
    }

    handleThemeToggle() {
        this.app.theme.toggleDarkMode();
    }
}