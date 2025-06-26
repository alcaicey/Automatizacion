// src/static/eventHandlers.js

window.eventHandlers = {
    // Maneja el clic en el botón de actualización principal
    async handleUpdateClick(isAutoUpdate = false) {
        if (window.app.state.isUpdating) {
            if (!isAutoUpdate) console.log("[App] Se ignoró el clic manual porque ya hay una actualización en curso.");
            return;
        }

        if (isAutoUpdate) {
            try {
                const statusRes = await fetch('/api/bot-status');
                const statusData = await statusRes.json();
                if (statusData.is_running) {
                    console.log('[App] Auto-actualización omitida, bot ya está ocupado.');
                    const select = document.getElementById('autoUpdateSelect');
                    if (select) autoUpdater.start(select.value, () => this.handleUpdateClick(true));
                    return;
                }
            } catch (e) {
                console.error("Error al comprobar estado del bot", e);
            }
        }

        window.app.state.isUpdating = true;
        if (!isAutoUpdate) {
            autoUpdater.stop();
        }
        
        window.app.updateRefreshButton();
        uiManager.toggleLoading(true, window.app.state.isFirstRun ? 'Iniciando navegador...' : 'Actualizando datos...');
        
        try {
            const response = await fetch('/api/stocks/update', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_auto_update: isAutoUpdate })
            });
            
            if (response.status === 409) throw new Error((await response.json()).message);
            if (!response.ok && response.status !== 200) throw new Error('Error desconocido del servidor.');
            if (response.status === 202) uiManager.updateStatus('Proceso de actualización iniciado.', 'info');

        } catch (error) {
            uiManager.updateStatus(`Error: ${error.message}`, 'danger');
            window.app.state.isUpdating = false;
            uiManager.toggleLoading(false);
            window.app.updateRefreshButton();
            
            if (isAutoUpdate) {
                const select = document.getElementById('autoUpdateSelect');
                if (select) autoUpdater.start(select.value, () => this.handleUpdateClick(true));
            }
        }
    },
    
    // Maneja el cambio en el selector de auto-actualización
    handleAutoUpdateChange(event) {
        const intervalValue = event.target.value;
        sessionStorage.setItem('autoUpdateInterval', intervalValue);
        
        if (intervalValue === "off") {
            autoUpdater.stop();
        } else {
            autoUpdater.start(intervalValue, () => this.handleUpdateClick(true));
        }
    },

    // Maneja el envío del formulario de filtro de acciones
    async handleFilterSubmit(event) {
        event.preventDefault();
        const form = event.target;
        window.app.state.stockFilters.codes = Array.from(form.querySelectorAll('.stock-code')).map(i => i.value.trim().toUpperCase());
        window.app.state.stockFilters.all = form.querySelector('#allStocksCheck').checked;
        
        await fetch('/api/filters', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(window.app.state.stockFilters)
        });
        
        // Pide a la app principal que recargue los datos
        await window.app.fetchAndDisplayStocks();
    },

    // Maneja el guardado de preferencias de columnas de la tabla de mercado
    async handleSaveColumnPrefs() {
        const form = document.getElementById('columnConfigForm');
        if (!form) return;
        
        const selectedColumns = Array.from(form.querySelectorAll('input:checked')).map(i => i.value);
        window.app.state.columnPrefs.visible = selectedColumns;
        
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
        window.app.renderAllTables();
    }
};