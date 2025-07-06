// src/static/eventHandlers.js

class EventHandlers {
    constructor(app) {
        this.app = app;
    }

    init() {
        // --- MANEJADOR CENTRAL DE EVENTOS DE WIDGETS ---
        document.addEventListener('widgetAdded', (e) => {
            const { element, widgetId } = e.detail;
            console.log(`[Event] Widget '${widgetId}' añadido al DOM.`);

            switch (widgetId) {
                case 'portfolio':
                    if (this.app.portfolioManager) {
                        console.log('[Event] Inicializando Portfolio Manager...');
                        this.app.portfolioManager.init(this.app, element);
                    }
                    break;
                case 'news':
                    if (this.app.newsManager) {
                        console.log('[Event] Inicializando News Manager...');
                        this.app.newsManager.init(this.app, element);
                    }
                    break;
                case 'alerts':
                    if (this.app.alertManager) {
                        console.log('[Event] Inicializando Alert Manager...');
                        this.app.alertManager.init(this.app, element);
                    }
                    break;
                case 'drainers':
                     if (this.app.drainerManager) {
                        console.log('[Event] Inicializando Drainer Manager...');
                        this.app.drainerManager.init(this.app, element);
                    }
                    break;
                case 'controls':
                    if (this.app.controlsManager) {
                        console.log('[Event] Inicializando Controls Manager...');
                        this.app.controlsManager.init(this.app, element);
                    }
                    break;
            }
        });

        // --- OTROS EVENTOS DE LA UI ---
        
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

        // Guardar preferencias de columnas del portafolio
        const savePortfolioPrefsBtn = document.getElementById('savePortfolioColumnPrefs');
        if (savePortfolioPrefsBtn) {
            savePortfolioPrefsBtn.addEventListener('click', () => {
                if (this.app.portfolioManager) this.app.portfolioManager.saveColumnPreferences();
            });
        }

        // Añadir activo al portafolio
        const addHoldingForm = document.getElementById('portfolioForm');
        if (addHoldingForm) {
            addHoldingForm.addEventListener('submit', (event) => {
                if (this.app.portfolioManager) this.app.portfolioManager.handleAdd(event);
            });
        }
        
        // Delegación de eventos para eliminar activos del portafolio
        document.body.addEventListener('click', (event) => {
            if (event.target.closest('.delete-holding-btn')) {
                const id = event.target.closest('.delete-holding-btn').dataset.id;
                if (this.app.portfolioManager) this.app.portfolioManager.handleDelete(id);
            }
        });
    }

    handleStockUpdate(prices) {
        const changedNemos = new Set();
        prices.forEach(price => {
            const currentStock = this.app.state.stockPriceMap.get(price.nemo);
            if (currentStock) {
                Object.assign(currentStock, price);
                changedNemos.add(price.nemo);
            }
        });
        this.app.uiManager.highlightUpdates(prices);
        this.app.portfolioManager.render(this.app.state.stockPriceMap, changedNemos);
        this.app.renderAllTables();
    }

    handleLastUpdate(timestamp) {
        this.app.state.timestamp = timestamp;
        this.app.uiManager.updateTimestamp(timestamp);
    }

    handleAlert(alert) {
        this.app.uiManager.showAlert(alert.message, alert.category, alert.timestamp);
    }

    // Maneja el clic en el botón de actualización principal
    async handleUpdateClick(isAutoUpdate = false) {
        if (this.app.state.isUpdating) {
            if (!isAutoUpdate) console.log("[App] Se ignoró el clic manual porque ya hay una actualización en curso.");
            return;
        }

        if (isAutoUpdate) {
            try {
                const statusRes = await fetch('/api/bot/status');
                const statusData = await statusRes.json();
                if (statusData.is_running) {
                    console.log('[App] Auto-actualización omitida, bot ya está ocupado.');
                    if (window.autoUpdater) {
                        const select = document.getElementById('autoUpdateSelect');
                        if (select) window.autoUpdater.start(select.value, () => this.handleUpdateClick(true));
                    }
                    return;
                }
            } catch (e) {
                console.error("Error al comprobar estado del bot", e);
            }
        }

        this.app.state.isUpdating = true;
        if (!isAutoUpdate && window.autoUpdater) {
            window.autoUpdater.stop();
        }
        
        this.app.uiManager.updateRefreshButton(
            '<div class="spinner-border spinner-border-sm" role="status"></div><span class="ms-2">Actualizando...</span>',
            true, 
            () => this.handleUpdateClick()
        );
        this.app.uiManager.toggleLoading(true, this.app.state.isFirstRun ? 'Iniciando navegador...' : 'Actualizando datos...');
        
        try {
            const response = await fetch('/api/stocks/update', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_auto_update: isAutoUpdate })
            });
            
            if (response.status === 409) throw new Error((await response.json()).message);
            if (!response.ok && response.status !== 200) throw new Error('Error desconocido del servidor.');
            if (response.status === 202) this.app.uiManager.updateStatus('Proceso de actualización iniciado.', 'info');

        } catch (error) {
            this.app.uiManager.updateStatus(`Error: ${error.message}`, 'danger');
            this.app.state.isUpdating = false;
            this.app.uiManager.toggleLoading(false);
            
            this.app.uiManager.updateRefreshButton(
                '<i class="fas fa-sync-alt me-2"></i>Actualizar Ahora',
                false,
                () => this.handleUpdateClick()
            );
            
            if (isAutoUpdate && window.autoUpdater) {
                const select = document.getElementById('autoUpdateSelect');
                if (select) window.autoUpdater.start(select.value, () => this.handleUpdateClick(true));
            }
        }
    }
    
    // Maneja el cambio en el selector de auto-actualización
    handleAutoUpdateChange(event) {
        const intervalValue = event.target.value;
        sessionStorage.setItem('autoUpdateInterval', intervalValue);
        
        if (intervalValue === "off") {
            autoUpdater.stop();
        } else {
            autoUpdater.start(intervalValue, () => this.handleUpdateClick(true));
        }
    }

    // Maneja el envío del formulario de filtro de acciones
    async handleFilterSubmit(event) {
        event.preventDefault();
        const form = event.target;
        this.app.state.stockFilters.codes = Array.from(form.querySelectorAll('.stock-code')).map(i => i.value.trim().toUpperCase());
        this.app.state.stockFilters.all = form.querySelector('#allStocksCheck').checked;
        
        await fetch('/api/filters', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.app.state.stockFilters)
        });
        
        // Pide a la app principal que recargue los datos
        await this.app.fetchAndDisplayStocks();
    }

    // Maneja el guardado de preferencias de columnas de la tabla de mercado
    async handleSaveColumnPrefs() {
        const form = document.getElementById('columnConfigForm');
        if (!form) return;
        
        const selectedColumns = Array.from(form.querySelectorAll('input:checked')).map(i => i.value);
        this.app.state.columnPrefs.visible = selectedColumns;
        
        await fetch('/api/columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: selectedColumns })
        });
        
        const modalElement = document.getElementById('columnConfigModal');
        if(modalElement) {
            bootstrap.Modal.getInstance(modalElement).hide();
        }
        
        // Pide a la app principal que re-renderice las tablas
        this.app.renderAllTables();
    }
}