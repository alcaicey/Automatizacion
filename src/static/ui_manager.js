// src/static/ui_manager.js

window.uiManager = {
    dataTable: null,
    dom: {},

    init() {
        this.dom = {
            statusMessage: document.getElementById('statusMessage'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            loadingMessage: document.getElementById('loadingMessage'),
            refreshBtn: document.getElementById('refreshBtn'),
            stocksTable: document.getElementById('stocksTable'),
            columnConfigForm: document.getElementById('columnConfigForm'),
            countdownTimer: document.getElementById('countdownTimer'),
            allStocksCheck: document.getElementById('allStocksCheck'),
            stockCodeInputs: document.querySelectorAll('.stock-code')
        };
        console.log('[UI] Módulo inicializado y elementos del DOM cacheados.');
    },

    updateStatus(message, type = 'info') {
        if (!this.dom.statusMessage) return;
        this.dom.statusMessage.innerHTML = `<i class="fas fa-info-circle me-2"></i><span>${message}</span>`;
        this.dom.statusMessage.className = `alert alert-${type} small py-2`;
    },

    toggleLoading(show, message = 'Cargando...') {
        if (!this.dom.loadingOverlay || !this.dom.loadingMessage) return;
        this.dom.loadingMessage.textContent = message;
        this.dom.loadingOverlay.classList.toggle('d-none', !show);
    },
    
    updateRefreshButton(text, isDisabled) {
        if (!this.dom.refreshBtn) return;
        this.dom.refreshBtn.innerHTML = `<i class="fas fa-sync-alt me-2"></i> ${text}`;
        this.dom.refreshBtn.disabled = isDisabled;
    },

    updateCountdown(text) {
        if (this.dom.countdownTimer) this.dom.countdownTimer.textContent = text;
    },
    
    renderColumnModal(allColumns, visibleColumns) {
        if (!this.dom.columnConfigForm) return;
        this.dom.columnConfigForm.innerHTML = '';
        allColumns.forEach(col => {
            const isChecked = visibleColumns.includes(col);
            this.dom.columnConfigForm.innerHTML += `
                <div class="col-6">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" value="${col}" id="col-check-${col}" ${isChecked ? 'checked' : ''}>
                        <label class="form-check-label" for="col-check-${col}">${col.replace(/_/g, ' ')}</label>
                    </div>
                </div>`;
        });
    },

    renderFilterInputs(stockFilters) {
        if (!this.dom.allStocksCheck || !this.dom.stockCodeInputs) return;
        this.dom.allStocksCheck.checked = stockFilters.all;
        this.dom.stockCodeInputs.forEach((input, index) => {
            input.value = stockFilters.codes[index] || '';
        });
    },

    renderTable(stocks, timestamp, visibleColumns) {
        console.log(`[UI] Recibida orden para renderizar tabla con ${stocks.length} registros y columnas:`, visibleColumns);
        if (this.dataTable) this.dataTable.destroy();
        
        const tableContainer = this.dom.stocksTable.parentElement;
        tableContainer.innerHTML = '<table id="stocksTable" class="table table-striped table-hover"></table>';
        this.dom.stocksTable = document.getElementById('stocksTable');

        if (!stocks || stocks.length === 0) {
            this.updateStatus('No hay datos para mostrar con el filtro actual.', 'warning');
            return;
        }

        const allHeadingsFromData = Object.keys(stocks[0]);
        const headingsToRender = visibleColumns.filter(h => allHeadingsFromData.includes(h));

        if (headingsToRender.length === 0) {
            console.error("[UI] Error: Ninguna de las columnas visibles seleccionadas existe en los datos recibidos. Mostrando todas como fallback.", "Visibles:", visibleColumns, "Disponibles:", allHeadingsFromData);
            headingsToRender.push(...allHeadingsFromData);
        }

        const tableData = stocks.map(stock =>
            headingsToRender.map(header => {
                const value = stock[header];
                if (typeof value === 'number') return value.toLocaleString('es-CL');
                return value !== undefined && value !== null ? value : 'N/A';
            })
        );
        
        this.dataTable = new simpleDatatables.DataTable(this.dom.stocksTable, {
            data: { headings: headingsToRender.map(h => h.replace(/_/g, ' ')), data: tableData },
            perPage: 50, perPageSelect: [25, 50, 100],
            searchable: true, sortable: true, fixedHeight: true,
        });

        this.updateStatus(`Mostrando ${stocks.length} acciones. Última actualización: ${timestamp}`, 'success');
        console.log("[UI] Tabla renderizada con éxito.");
    }
};