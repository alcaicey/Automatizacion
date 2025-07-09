// src/static/js/app.js

window.addEventListener('error', (event) => {
    console.error('ERROR GLOBAL NO CAPTURADO:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
    });
    
    // Opcional: Mostrar un mensaje genérico al usuario para recargar
    const errorId = 'global-error-banner';
    if (document.getElementById(errorId)) return; // No mostrar múltiples banners

    const errorDiv = document.createElement('div');
    errorDiv.id = errorId;
    errorDiv.className = 'alert alert-danger position-fixed top-0 start-0 w-100 rounded-0 text-center';
    errorDiv.style.zIndex = '2000';
    errorDiv.innerHTML = 'Ocurrió un error inesperado. Se recomienda <a href="#" onclick="location.reload()">recargar la página</a>.';
    document.body.prepend(errorDiv);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('PROMESA RECHAZADA NO CAPTURADA:', event.reason);
});

import UIManager from './managers/uiManager.js';
import Theme from './utils/theme.js';
import AutoUpdater from './utils/autoUpdater.js';
import CommandPalette from './utils/commandPalette.js';
import EventHandlers from './utils/eventHandlers.js';
import DashboardLayout from './utils/dashboardLayout.js';
import BotStatusManager from './managers/botStatusManager.js';
import AlertManager from './managers/alertManager.js';
import PortfolioManager from './managers/portfolioManager.js';
import ClosingManager from './managers/closingManager.js';
import NewsManager from './managers/newsManager.js';
import DrainerManager from './managers/drainerManager.js';
import DividendManager from './managers/dividendManager.js';
import KpiManager from './managers/kpiManager.js';

// --- INICIO DE LA MODIFICACIÓN ---
// Importación dinámica de la página del Dashboard
import Dashboard from './pages/dashboard.js';
// --- FIN DE LA MODIFICACIÓN ---


class App {
    constructor() {
        console.log('[App] Constructor llamado. Creando instancias de los managers...');
        this.socket = io({
            transports: ['websocket', 'polling']
        });
        
        this.uiManager = new UIManager(this);
        this.theme = new Theme(this);
        this.autoUpdater = new AutoUpdater(this);
        this.commandPalette = new CommandPalette(this);
        
        // Managers de Widgets/Módulos
        this.botStatusManager = new BotStatusManager(this);
        this.alertManager = new AlertManager(this);
        this.portfolioManager = new PortfolioManager(this);
        this.closingManager = new ClosingManager(this);
        this.newsManager = new NewsManager(this);
        this.drainerManager = new DrainerManager(this);
        this.dividendManager = new DividendManager(this);
        this.kpiManager = new KpiManager(this);
        
        this.eventHandlers = new EventHandlers(this);
        this.dashboardLayout = new DashboardLayout(this);
        
        console.log('[App] Instancias de managers creadas.');
    }

    async initialize() {
        console.log('[App] Inicialización comenzando...');
        try {
            this.uiManager.initialize();
            this.theme.initialize();
            this.eventHandlers.initialize();
            
            const page = document.body.dataset.page;
            console.log(`[App] Detectada página: ${page}`);

            if (page === 'dashboard') {
                console.log('[App] Inicializando layout del dashboard...');
                await this.dashboardLayout.initialize();
                
                // --- INICIO DE LA MODIFICACIÓN ---
                // Se instancia y se inicializa el dashboard después de que el layout está listo.
                this.dashboard = new Dashboard(this);
                this.dashboard.initialize();
                // --- FIN DE LA MODIFICACIÓN ---

                console.log('[App] Layout y página del dashboard inicializados.');

            } else if (page === 'login') {
                console.log('[App] Inicializando página de login...');
                const loginScript = await import('./pages/login.js');
                const login = new loginScript.default(this);
                login.initialize();
                console.log('[App] Página de login inicializada.');
            } else if (page === 'historico') {
                // ...
            }
            
            this.commandPalette.initialize();
            this.autoUpdater.initialize();
            console.log('[App] Inicialización completada con éxito.');
        } catch (error) {
            console.error('[App] Error catastrófico durante la inicialización:', error);
            this.uiManager.toggleLoading(true, 'Error crítico. Revise la consola.');
        } finally {
            console.log('[App] Ocultando overlay de carga principal.');
            this.uiManager.toggleLoading(false); // Asegurarse de que el loader principal se oculte
        }
    }

    // --- Lógica de Widgets (para actuar como WidgetManager) ---

    getWidgetManager(widgetId) {
        const map = {
            'portfolio': this.portfolioManager,
            'news': this.newsManager,
            'price-alerts': this.alertManager,
            'bot-status': this.botStatusManager,
            // 'stock-filter' es manejado por eventHandlers directamente, no tiene un manager dedicado
        };
        return map[widgetId];
    }

    getAllWidgetsInfo() {
        // Devuelve la información que dashboardLayout necesita para el menú "Añadir Widget"
        return [
            { id: 'portfolio', name: 'Mi Portafolio', manager: this.portfolioManager },
            { id: 'news', name: 'Últimas Noticias', manager: this.newsManager },
            { id: 'price-alerts', name: 'Alertas de Precio', manager: this.alertManager },
            { id: 'bot-status', name: 'Estado del Bot', manager: this.botStatusManager },
            { id: 'stock-filter', name: 'Configuración y Acciones' },
            { id: 'kpi-table', name: 'Tabla de KPIs Avanzados' },
            { id: 'dividend-table', name: 'Tabla de Dividendos' },
            { id: 'closing-table', name: 'Tabla de Cierres' },
            { id: 'drainer-table', name: 'Análisis de Adelantamientos' },
        ];
    }
    
    // --- Lógica de Formato y Columnas ---

    /**
     * Define las columnas base para una tabla, con títulos y tipos de datos.
     * @param {string} type - 'portfolio', 'closing', etc.
     * @returns {Array<object>}
     */
    getBaseColumns(type) {
        // Podríamos tener diferentes definiciones base por tipo de tabla
        const definitions = {
            portfolio: [
                { data: 'symbol', title: 'Símbolo' },
                { data: 'quantity', title: 'Cantidad' },
                { data: 'purchase_price', title: 'P. Compra' },
                { data: 'total_paid', title: 'Total Pagado' },
                { data: 'current_price', title: 'Precio Actual' },
                { data: 'daily_variation_percent', title: 'Var. % Día' },
                { data: 'current_value', title: 'Valor Actual' },
                { data: 'gain_loss_total', title: 'G/P ($)' },
                { data: 'gain_loss_percent', title: 'G/P (%)' },
                { data: 'actions', title: 'Acc' }
            ]
            // ... otras definiciones para 'closing', 'market', etc.
        };
        return definitions[type] || [];
    }
    
    /**
     * Aplica renderizadores de formato a una lista de columnas.
     * @param {Array<object>} columns - Array de columnas base.
     * @returns {Array<object>} - Columnas con la función `render` añadida.
     */
    applyColumnRenderers(columns) {
        const currencyRenderer = this.uiManager.createNumberRenderer(false, 'es-CL', { style: 'currency', currency: 'CLP' });
        const numberRenderer = this.uiManager.createNumberRenderer();
        const percentRenderer = this.uiManager.createNumberRenderer(true);

        const rendererMap = {
            'purchase_price': currencyRenderer,
            'total_paid': currencyRenderer,
            'current_price': currencyRenderer,
            'current_value': currencyRenderer,
            'gain_loss_total': currencyRenderer,
            'quantity': numberRenderer,
            'daily_variation_percent': percentRenderer,
            'gain_loss_percent': percentRenderer,
        };

        return columns.map(col => {
            if (rendererMap[col.data]) {
                return { ...col, render: rendererMap[col.data] };
            }
            return col;
        });
    }

    // --- Lógica de Datos ---

    async fetchData(url, options = {}, timeout = 15000) { // Timeout de 15 segundos por defecto
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            console.warn(`Petición a ${url} superó el timeout de ${timeout}ms. Abortando.`);
            controller.abort();
        }, timeout);
    
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal // Asociar el AbortController
            });
    
            clearTimeout(timeoutId); // Limpiar el timeout si la respuesta llega a tiempo
    
            if (!response.ok) {
                // Intentar leer el error del cuerpo de la respuesta JSON del manejador global
                try {
                    const errorData = await response.json();
                    // Usar el mensaje del error del backend si está disponible, sino, uno genérico
                    throw new Error(errorData.message || `Error del servidor: ${response.status}`);
                } catch (jsonError) {
                    // Si el cuerpo no es JSON o hay otro error, usar el status text
                    throw new Error(`Error en la respuesta HTTP: ${response.status} ${response.statusText}`);
                }
            }
            // Si la respuesta es 204 No Content, no intentar parsear JSON
            if (response.status === 204) {
                return null;
            }
            return await response.json();
    
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                console.error(`Petición abortada por timeout: ${url}`);
                // Lanzar un error más amigable para ser capturado por los managers
                throw new Error('El servidor tardó demasiado en responder.');
            }
            // Re-lanzar otros errores para que sean manejados por quien llamó a la función
            console.error(`Error en fetchData para ${url}:`, error.message);
            throw error; 
        }
    }

    getChangedNemos(newPriceMap) {
        const changed = new Set();
        if (!this.lastPriceMap) {
            this.lastPriceMap = newPriceMap;
            return changed;
        }

        for (const [nemo, price] of newPriceMap.entries()) {
            if (this.lastPriceMap.get(nemo) !== price) {
                changed.add(nemo);
            }
        }
        this.lastPriceMap = newPriceMap;
        return changed;
    }
    
    renderAllTables(changedNemos = new Set()) {
        if (!this.allStocks || this.allStocks.length === 0) return;

        const portfolioData = this.portfolioManager.getDisplayData(this.allStocks);

        // 1. Construir la configuración de columnas con los renderers de formato
        const portfolioColumnConfig = {};
        this.portfolioManager.state.columnPrefs.all.forEach(col => {
            const config = { title: col.title };
            const currencyOptions = { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 };

            if (['total_paid', 'current_value', 'gain_loss_total', 'purchase_price', 'current_price'].includes(col.id)) {
                config.render = this.uiManager.createNumberRenderer(false, 'es-CL', currencyOptions);
            } else if (['gain_loss_percent', 'daily_variation_percent'].includes(col.id)) {
                config.render = this.uiManager.createNumberRenderer(true); // isPercentage = true
            } else if (col.id === 'quantity') {
                config.render = this.uiManager.createNumberRenderer();
            } else {
                config.render = (data, type, row) => data !== null && data !== undefined ? data : 'N/A';
            }
            portfolioColumnConfig[col.id] = config;
        });
        
        // 2. Determinar el orden de las columnas visibles
        const visibleColumns = this.portfolioManager.state.columnPrefs.visible
            .map(id => portfolioColumnConfig[id])
            .filter(Boolean); // Filtrar por si alguna pref no tiene config

        // 3. Renderizar o actualizar la tabla
        this.uiManager.renderDataTable('#portfolio-table', portfolioData, visibleColumns, changedNemos);
    }

    clearObsoleteLayout() {
        const savedLayout = localStorage.getItem('dashboardLayout');
        if (savedLayout) {
            try {
                const parsedLayout = JSON.parse(savedLayout);
                // Si el layout guardado no tiene el widget 'bot-status', se considera obsoleto.
                if (!parsedLayout.some(widget => widget.id === 'bot-status')) {
                    console.warn('[App] Layout obsoleto detectado (sin bot-status). Se eliminará para forzar el layout por defecto.');
                    localStorage.removeItem('dashboardLayout');
                }
            } catch (e) {
                console.error('[App] Error al parsear el layout guardado. Se eliminará para seguridad.', e);
                localStorage.removeItem('dashboardLayout');
            }
        }
    }
}

// Punto de entrada principal
document.addEventListener('DOMContentLoaded', () => {
    console.log('[App] DOM completamente cargado y parseado.');
    const app = new App();
    window.app = app;
    app.initialize();
});