// src/static/app.js

window.app = {
    // ---- 1. ESTADO GLOBAL DE LA APLICACIÓN ----
    state: {
        isUpdating: false,
        isFirstRun: true,
        stockPriceMap: new Map(),
        stockData: [],
        timestamp: '--',
        columnPrefs: {
            all: [],
            visible: [],
            config: {
                'NEMO': { title: 'Símbolo' },
                'PRECIO_CIERRE': { title: 'Precio', render: uiManager.createNumberRenderer() },
                'VARIACION': { title: 'Var. %', render: uiManager.createNumberRenderer(true) },
                'PRECIO_COMPRA': { title: 'P. Compra', render: uiManager.createNumberRenderer() },
                'PRECIO_VENTA': { title: 'P. Venta', render: uiManager.createNumberRenderer() },
                'MONTO': { title: 'Monto Transado', render: uiManager.createNumberRenderer(false, 'es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }) },
                'UN_TRANSADAS': { title: 'Unidades', render: uiManager.createNumberRenderer() }
            }
        },
        stockFilters: { codes: [], all: true }
    },
    
    socket: null,

    // ---- 2. INICIALIZACIÓN Y ORQUESTACIÓN ----
    init() {
        this.setupWebSocket();

        uiManager.init();
        portfolioManager.init();
        closingManager.init(this.socket);
        drainerManager.init(this.socket);
        if (window.controlsManager) {
            controlsManager.init();
        }
        autoUpdater.init();
        
        this.attachEventListeners();
        
        setTimeout(() => {
            console.log('[App] El DOM está listo. Iniciando carga de datos...');
            this.initializeApp();
        }, 100);
    },
    
    async initializeApp() {
        uiManager.updateStatus('Inicializando...', 'info');
        this.updateRefreshButton();
        
        await this.loadPreferences();
        await portfolioManager.loadHoldings();
        this.renderAllTables();

        if (window.closingManager && document.getElementById('closingTable')) {
            await closingManager.loadPreferences();
            await closingManager.loadClosings();
        }
        
        await this.fetchAndDisplayStocks();
        
        const savedInterval = sessionStorage.getItem('autoUpdateInterval');
        const autoUpdateSelect = document.getElementById('autoUpdateSelect');
        if (savedInterval && autoUpdateSelect) {
            autoUpdateSelect.value = savedInterval;
        }
        console.log('[App] Aplicación inicializada por completo.');
    },
    
    // ---- 3. LÓGICA DE DATOS Y RENDERIZADO ----
    async loadPreferences() {
        try {
            const [colsRes, filtersRes] = await Promise.all([fetch('/api/columns'), fetch('/api/filters')]);
            if (!colsRes.ok || !filtersRes.ok) throw new Error('No se pudieron cargar las preferencias.');
            
            const colsData = await colsRes.json();
            this.state.columnPrefs.all = colsData.all_columns;
            this.state.columnPrefs.visible = colsData.visible_columns;
            
            const filtersData = await filtersRes.json();
            this.state.stockFilters = { codes: filtersData.codes, all: filtersData.all !== false };
            
            uiManager.renderColumnModal(this.state.columnPrefs.all, this.state.columnPrefs.visible, this.state.columnPrefs.config);
            uiManager.renderFilterInputs(this.state.stockFilters);
        } catch (error) {
            console.error("Error en loadPreferences:", error);
            uiManager.updateStatus('Error al cargar preferencias.', 'danger');
        }
    },

    async fetchAndDisplayStocks() {
        const codes = this.state.stockFilters.all ? [] : this.state.stockFilters.codes.filter(Boolean);
        const url = new URL(window.location.origin + '/api/stocks');
        if (codes.length > 0) {
            codes.forEach(code => url.searchParams.append('code', code));
        }
        
        try {
            const response = await fetch(url);
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Error del servidor');
            
            this.state.stockData = result.data || [];
            this.state.timestamp = result.timestamp || '--';
            
            this.state.stockPriceMap.clear();
            this.state.stockData.forEach(stock => this.state.stockPriceMap.set(stock.NEMO, stock));

            this.renderAllTables();
        } catch (error) {
            console.error("Error en fetchAndDisplayStocks:", error);
            uiManager.updateStatus(`Error al cargar datos: ${error.message}`, 'danger');
        }
    },
    
    renderAllTables() {
        uiManager.renderTable(this.state.stockData, this.state.timestamp, this.state.columnPrefs.visible, this.state.columnPrefs.config);
        portfolioManager.render(this.state.stockPriceMap);
    },

    updateRefreshButton() {
        let text = this.state.isFirstRun ? 'Iniciar Navegador' : 'Actualizar Ahora';
        if (this.state.isUpdating) {
            text = `<i class="fas fa-spinner fa-spin me-2"></i>` + (this.state.isFirstRun ? 'Iniciando...' : 'Actualizando...');
        } else {
            text = `<i class="fas fa-sync-alt me-2"></i>` + text;
        }
        uiManager.updateRefreshButton(text, this.state.isUpdating);
    },

    // ---- 4. WEBSOCKETS Y EVENT LISTENERS ----
    setupWebSocket() {
        this.socket = io();
        this.socket.on('connect', () => uiManager.updateStatus('Conectado al servidor.', 'success'));
        this.socket.on('disconnect', () => uiManager.updateStatus('Desconectado.', 'danger'));

        this.socket.on('initial_session_ready', () => {
            this.state.isUpdating = false;
            this.state.isFirstRun = false;
            uiManager.toggleLoading(false);
            this.updateRefreshButton();
            uiManager.updateStatus("Navegador listo. Puede iniciar la captura de datos.", 'success');
            
            const select = document.getElementById('autoUpdateSelect');
            if (select && select.value !== 'off' && !sessionStorage.getItem('autoUpdateTarget')) {
                eventHandlers.handleUpdateClick(true);
            }
        });
        
        this.socket.on('new_data', async () => {
            this.state.isUpdating = false;
            uiManager.toggleLoading(false);
            this.updateRefreshButton();
            uiManager.updateStatus("¡Nuevos datos recibidos! Actualizando...", 'success');
            await this.fetchAndDisplayStocks();
            
            const select = document.getElementById('autoUpdateSelect');
            if (select && select.value !== 'off') {
                autoUpdater.start(select.value, () => eventHandlers.handleUpdateClick(true));
            }
        });

        this.socket.on('bot_error', (data) => {
            this.state.isUpdating = false;
            uiManager.toggleLoading(false);
            this.updateRefreshButton();
            uiManager.updateStatus(`Error del bot: ${data.message}`, 'danger');
            
            const select = document.getElementById('autoUpdateSelect');
            if (select && select.value !== 'off') {
                autoUpdater.start(select.value, () => eventHandlers.handleUpdateClick(true));
            }
        });
    },

    attachEventListeners() {
        // La lógica está ahora en eventHandlers.js, aquí solo conectamos los eventos
        $(document.body).on('click', '#refreshBtn', () => eventHandlers.handleUpdateClick(false));
        $(document.body).on('change', '#autoUpdateSelect', (e) => eventHandlers.handleAutoUpdateChange(e));
        $(document.body).on('click', '#saveColumnPrefs', () => eventHandlers.handleSaveColumnPrefs());
    }
};

// ---- INICIAR LA APLICACIÓN ----
document.addEventListener('dashboardReady', () => {
    console.log("Evento 'dashboardReady' detectado. Iniciando app.js...");
    window.app.init();
});