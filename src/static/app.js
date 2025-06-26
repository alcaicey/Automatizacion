// src/static/app.js

window.app = {
    // ---- 1. ESTADO GLOBAL DE LA APLICACIÓN (SIN CAMBIOS) ----
    state: {
        isUpdating: false,
        isFirstRun: true,
        stockPriceMap: new Map(),
        stockData: [],
        timestamp: '--',
        columnPrefs: {
            all: [],
            visible: [],
            config: { // Mantener la configuración de renderizado aquí
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
    
    // ---- 2. INICIALIZACIÓN (SIN CAMBIOS EN LA LÓGICA INTERNA) ----
    init() {
        uiManager.init();
        portfolioManager.init();
        closingManager.init();
        autoUpdater.init(uiManager); 
        this.initializeApp();
        this.setupWebSocket();
        this.attachEventListeners();
        console.log('[App] Aplicación inicializada por completo.');
    },
    
    async initializeApp() {
        uiManager.updateStatus('Inicializando...', 'info');
        this.updateRefreshButton();

        // 1. Cargamos todas las preferencias y el portafolio en paralelo.
        await Promise.all([
            this.loadPreferences(), 
            portfolioManager.loadHoldings(),
            closingManager.loadPreferences()
        ]);

        // 2. Cargamos los datos de las acciones de mercado.
        await this.fetchAndDisplayStocks();
        
        // 3. AHORA, con el portafolio ya cargado, llamamos a la carga de datos de cierre.
        if (window.closingManager) {
            await window.closingManager.loadClosings();
        }
        
        const savedInterval = sessionStorage.getItem('autoUpdateInterval');
        if (savedInterval) {
            uiManager.dom.autoUpdateSelect.value = savedInterval;
        }
    },
    
    // ---- 3. LÓGICA DE DATOS (SIN CAMBIOS) ----
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

    // ---- 4. MANEJO DE ESTADO Y EVENTOS (SIN CAMBIOS) ----
    updateRefreshButton() {
        let text = this.state.isFirstRun ? 'Iniciar Navegador' : 'Actualizar Ahora';
        if (this.state.isUpdating) {
            text = `<i class="fas fa-spinner fa-spin me-2"></i>` + (this.state.isFirstRun ? 'Iniciando...' : 'Actualizando...');
        } else {
            text = `<i class="fas fa-sync-alt me-2"></i>` + text;
        }
        uiManager.updateRefreshButton(text, this.state.isUpdating);
    },

    async handleUpdateClick(isAutoUpdate = false) {
        if (this.state.isUpdating) return;
        this.state.isUpdating = true;
        
        if (!isAutoUpdate) {
            autoUpdater.stop();
        }
        
        this.updateRefreshButton();
        uiManager.toggleLoading(true, this.state.isFirstRun ? 'Iniciando navegador...' : 'Actualizando datos...');
        
        try {
            const response = await fetch('/api/stocks/update', { method: 'POST' });
            if (!response.ok) throw new Error((await response.json()).message);
            uiManager.updateStatus('Proceso de actualización iniciado.', 'info');
        } catch (error) {
            uiManager.updateStatus(`Error: ${error.message}`, 'danger');
            this.state.isUpdating = false;
            uiManager.toggleLoading(false);
            this.updateRefreshButton();
            
            if (isAutoUpdate) {
                 autoUpdater.start(uiManager.dom.autoUpdateSelect.value, () => this.handleUpdateClick(true));
            }
        }
    },
    
    handleAutoUpdateChange() {
        const intervalValue = uiManager.dom.autoUpdateSelect.value;
        sessionStorage.setItem('autoUpdateInterval', intervalValue);
        
        if (intervalValue === "off") {
            autoUpdater.stop();
        } else {
            autoUpdater.start(intervalValue, () => this.handleUpdateClick(true));
        }
    },

    async handleFilterSubmit(event) {
        event.preventDefault();
        this.state.stockFilters.codes = Array.from(uiManager.dom.stockCodeInputs).map(i => i.value.trim().toUpperCase());
        this.state.stockFilters.all = uiManager.dom.allStocksCheck.checked;
        await fetch('/api/filters', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.state.stockFilters)
        });
        await this.fetchAndDisplayStocks();
    },

    async handleSaveColumnPrefs() {
        const selectedColumns = Array.from(uiManager.dom.columnConfigForm.querySelectorAll('input:checked')).map(i => i.value);
        this.state.columnPrefs.visible = selectedColumns;
        await fetch('/api/columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: selectedColumns })
        });
        bootstrap.Modal.getInstance(uiManager.dom.columnConfigModal).hide();
        this.renderAllTables();
    },

    // ---- 5. CONFIGURACIÓN DE WEBSOCKETS (SIN CAMBIOS) ----
    setupWebSocket() {
        const socket = io();
        socket.on('connect', () => uiManager.updateStatus('Conectado al servidor.', 'success'));
        socket.on('disconnect', () => uiManager.updateStatus('Desconectado.', 'danger'));

        socket.on('initial_session_ready', () => {
            this.state.isUpdating = false;
            this.state.isFirstRun = false;
            uiManager.toggleLoading(false);
            this.updateRefreshButton();
            uiManager.updateStatus("Navegador listo. Puede iniciar la captura de datos.", 'success');
            
            const intervalValue = uiManager.dom.autoUpdateSelect.value;
            const isTimerRunning = sessionStorage.getItem('autoUpdateTarget');
            if (intervalValue !== 'off' && !isTimerRunning) {
                this.handleUpdateClick(true);
            }
        });
        
        socket.on('new_data', async () => {
            this.state.isUpdating = false;
            uiManager.toggleLoading(false);
            this.updateRefreshButton();
            uiManager.updateStatus("¡Nuevos datos recibidos! Actualizando...", 'success');
            await this.fetchAndDisplayStocks();
            
            const intervalValue = uiManager.dom.autoUpdateSelect.value;
            if (intervalValue !== 'off') {
                autoUpdater.start(intervalValue, () => this.handleUpdateClick(true));
            }
        });

        socket.on('bot_error', (data) => {
            this.state.isUpdating = false;
            uiManager.toggleLoading(false);
            this.updateRefreshButton();
            uiManager.updateStatus(`Error del bot: ${data.message}`, 'danger');
            
            const intervalValue = uiManager.dom.autoUpdateSelect.value;
             if (intervalValue !== 'off') {
                autoUpdater.start(intervalValue, () => this.handleUpdateClick(true));
            }
        });
    },

    // ---- 6. ASIGNACIÓN DE EVENT LISTENERS (SIN CAMBIOS) ----
    attachEventListeners() {
        // Necesitamos asegurarnos de que los elementos existan antes de añadir listeners.
        // Delegación de eventos es una buena alternativa, pero por ahora, esto funcionará
        // ya que attachEventListeners se llama desde init(), que ahora espera al dashboard.
        
        $(uiManager.dom.refreshBtn).on('click', () => this.handleUpdateClick(false));
        $(uiManager.dom.autoUpdateSelect).on('change', () => this.handleAutoUpdateChange());
        
        // Los formularios están dentro de widgets, por lo que podrían no existir siempre.
        // Hacemos una comprobación antes de añadir el listener.
        if(uiManager.dom.stockFilterForm) {
            $(uiManager.dom.stockFilterForm).on('submit', (e) => this.handleFilterSubmit(e));
        }
        if(uiManager.dom.clearFilterBtn) {
            $(uiManager.dom.clearFilterBtn).on('click', () => {
                if (uiManager.dom.stockFilterForm) {
                    uiManager.dom.stockFilterForm.reset();
                    uiManager.dom.allStocksCheck.checked = true;
                    $(uiManager.dom.stockFilterForm).trigger('submit');
                }
            });
        }
        if(uiManager.dom.saveColumnPrefsBtn) {
            $(uiManager.dom.saveColumnPrefsBtn).on('click', () => this.handleSaveColumnPrefs());
        }

        if(portfolioManager.dom.form) {
            $(portfolioManager.dom.form).on('submit', (e) => portfolioManager.handleAdd(e));
        }
        // Para la tabla, usamos delegación de eventos, que es más robusto.
        $(portfolioManager.dom.tableBody).on('click', '.delete-holding-btn', function() {
            portfolioManager.handleDelete($(this).data('id'));
        });
    }
};

// ---- INICIAR LA APLICACIÓN (ÚNICA MODIFICACIÓN IMPORTANTE) ----

// -- Antes (Problemático) --
// $(document).ready(() => {
//     window.app.init();
// });

// -- Ahora (Correcto) --
// Escuchamos el evento personalizado que dispara dashboardLayout.js cuando ha terminado de crear los widgets.
// Esto garantiza que todos los elementos del DOM (tablas, formularios) existen antes de que app.js intente usarlos.
document.addEventListener('dashboardReady', () => {
    console.log("Evento 'dashboardReady' detectado. Iniciando app.js...");
    window.app.init();
});