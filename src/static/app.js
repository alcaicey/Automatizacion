// src/static/app.js

class App {
    constructor() {
        console.log('[App] Constructor llamado.');

        // Asignación correcta: Clases con 'new', Objetos directamente.
        this.uiManager = uiManager;
        this.portfolioManager = portfolioManager;
        this.closingManager = closingManager;
        this.newsManager = newsManager;
        this.alertManager = new AlertManager(this); // AlertManager es una CLASE
        this.drainerManager = drainerManager;
        this.controlsManager = controlsManager;
        this.autoUpdater = autoUpdater;
        this.eventHandlers = new EventHandlers(this); // EventHandlers es una CLASE
        this.dashboardLayout = new DashboardLayout();

        // Estado inicial
        this.state = {
            stocks: [],
            closings: [],
            portfolio: [],
            columnPrefs: {
                all: [],
                visible: []
            }
        };

        // Iniciar la aplicación
        this.initializeApp();
    }

    initializeApp() {
        console.log('[App] Aplicación inicializándose...');
        
        this.uiManager.init(this);
        this.autoUpdater.init(this);
        this.eventHandlers.init(this);
        this.dashboardLayout.init(this); // Pasar 'app' como widgetManager

        // CORRECCIÓN: Asignar el estado y el handler inicial al botón de actualizar.
        this.uiManager.updateRefreshButton(
            '<i class="fas fa-sync-alt me-2"></i>Actualizar Ahora',
            false, // Habilitado por defecto
            () => this.eventHandlers.handleUpdateClick() // Asignar el handler correcto
        );

        document.addEventListener('dashboardReady', () => {
            console.log('[App] Evento dashboardReady recibido. Carga inicial de UI completada.');
            // La carga de datos de widgets individuales ahora es manejada por sus respectivos managers
            // a través del evento 'widgetAdded'. Aquí solo ocultamos el overlay principal.
            this.uiManager.toggleLoading(false);
        }, { once: true });

        document.dispatchEvent(new Event('dashboardReady'));
        
        console.log('[App] Aplicación inicializada por completo.');
    }

    // --- Lógica de Widgets (para actuar como WidgetManager) ---

    loadWidget(widgetId, addToLayout) {
        // Lógica para mostrar un widget. Podríamos moverla de uiManager aquí.
        this.uiManager.showWidget(widgetId, addToLayout);
    }

    getAllWidgetsInfo() {
        // Devuelve la información que dashboardLayout necesita para el menú "Añadir Widget"
        return [
            { id: 'portfolio', name: 'Mi Portafolio' },
            { id: 'stock-filter', name: 'Configuración y Acciones' },
            { id: 'news', name: 'Últimas Noticias' },
            { id: 'price-alerts', name: 'Alertas de Precio' },
            { id: 'bot-status', name: 'Estado del Bot' }
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

    async fetchData(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Error en la respuesta del servidor: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error al realizar la petición a ${url}:`, error);
            this.uiManager.updateStatus(`No se pudo conectar al servidor.`, 'danger');
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
    // Limpieza de layout obsoleto para evitar errores de widgets fantasma.
    // Esto se puede comentar o eliminar una vez que el layout de los usuarios se haya actualizado.
    localStorage.removeItem('dashboardLayout');

    const app = new App();
    window.app = app; // Exponer para acceso global si es necesario
});