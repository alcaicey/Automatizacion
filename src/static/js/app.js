// src/static/js/app.js

// Captura global de errores para depuración
window.addEventListener("error", function (e) {
    console.error("Error capturado:", e.message, e.filename, e.lineno, e.error);
});
window.addEventListener("unhandledrejection", function (e) {
    console.error("Promesa no manejada:", e.reason);
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
        // this.uiManager.toggleLoading(false); // Llamada de depuración para forzar ocultar el overlay
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

    async fetchData(url, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            console.warn(`[API] La petición a ${url} ha superado el tiempo de espera de 15s. Abortando...`);
            controller.abort();
        }, 15000); // 15 segundos de timeout

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            if (!response.ok) {
                throw new Error(`Error en la respuesta del servidor: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                const errorMessage = `La petición a ${url} fue cancelada por timeout.`;
                console.error(errorMessage);
                this.uiManager.showFeedback('warning', 'El servidor tarda demasiado en responder.');
                throw new Error(errorMessage);
            }
            console.error(`Error al realizar la petición a ${url}:`, error);
            this.uiManager.updateStatus(`No se pudo conectar al servidor.`, 'danger');
            throw error;
        } finally {
            clearTimeout(timeoutId);
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
            } else if (['daily_variation_percent', 'gain_loss_percent'].includes(col.id)) {
                config.render = this.uiManager.createNumberRenderer(true);
            } else if (col.id === 'quantity') {
                config.render = this.uiManager.createNumberRenderer();
            }
            portfolioColumnConfig[col.id] = config;
        });
        
        // 2. Construir el array de columnas para DataTables usando las columnas visibles
        const visibleColumns = this.portfolioManager.state.columnPrefs.visible;
        const portfolioColumns = visibleColumns.map(key => ({
            data: key,
            title: portfolioColumnConfig[key]?.title || key
        }));

        // 3. Renderizar la tabla
        this.uiManager.renderTable(
            portfolioData,
            'portfolioTable',
            portfolioColumnConfig,
            portfolioColumns
        );

        // 4. Renderizar el resumen/totales
        this.portfolioManager.renderSummary(portfolioData);
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
    // Limpieza de layout obsoleto para evitar errores de widgets fantasma.
    localStorage.removeItem('dashboardLayout');

    const app = new App();
    window.app = app;
    app.initialize();
});