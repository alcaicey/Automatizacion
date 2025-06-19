// src/static/js/uiManager.js

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
            saveColumnPrefsBtn: document.getElementById('saveColumnPrefs'),
            columnConfigModal: document.getElementById('columnConfigModal'),
            stockFilterForm: document.getElementById('stockFilterForm'),
            clearFilterBtn: document.getElementById('clearBtn'),
            countdownTimer: document.getElementById('countdownTimer'),
            allStocksCheck: document.getElementById('allStocksCheck'),
            stockCodeInputs: document.querySelectorAll('.stock-code'),
            lastUpdate: document.getElementById('lastUpdate'),
            autoUpdateSelect: document.getElementById('autoUpdateSelect')
        };
        console.log('[UI] Módulo inicializado y DOM cacheado.');
    },

    updateStatus(message, type = 'info') {
        if (!this.dom.statusMessage) return;
        const icons = { info: 'info-circle', success: 'check-circle', warning: 'exclamation-triangle', danger: 'x-circle' };
        this.dom.statusMessage.innerHTML = `<i class="fas fa-${icons[type]} me-2"></i><span>${message}</span>`;
        this.dom.statusMessage.className = `alert alert-${type} small py-2`;
    },

    toggleLoading(show, message = 'Cargando...') {
        if (!this.dom.loadingOverlay || !this.dom.loadingMessage) return;
        this.dom.loadingMessage.textContent = message;
        this.dom.loadingOverlay.classList.toggle('d-none', !show);
    },
    
    updateRefreshButton(text, isDisabled) {
        if (!this.dom.refreshBtn) return;
        this.dom.refreshBtn.innerHTML = text;
        this.dom.refreshBtn.disabled = isDisabled;
    },

    updateCountdown(text) {
        if (this.dom.countdownTimer) this.dom.countdownTimer.textContent = text;
    },
    
    renderColumnModal(allColumns, visibleColumns, config) {
        if (!this.dom.columnConfigForm) return;
        this.dom.columnConfigForm.innerHTML = '';
        allColumns.forEach(col => {
            const isChecked = visibleColumns.includes(col);
            const label = (config[col] && config[col].title) || col.replace(/_/g, ' ');
            this.dom.columnConfigForm.innerHTML += `
                <div class="col-6"><div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${col}" id="col-check-${col}" ${isChecked ? 'checked' : ''}>
                    <label class="form-check-label" for="col-check-${col}">${label}</label>
                </div></div>`;
        });
    },

    renderFilterInputs(stockFilters) {
        if (!this.dom.allStocksCheck || !this.dom.stockCodeInputs) return;
        this.dom.allStocksCheck.checked = stockFilters.all;
        this.dom.stockCodeInputs.forEach((input, index) => {
            input.value = stockFilters.codes[index] || '';
        });
    },
    
    createNumberRenderer(isPercent = false, locale = 'es-CL', options = {}) {
        return function(data, type, row) {
            if (type === 'display') {
                if (data === null || data === undefined || data === '') return 'N/A';
                const number = parseFloat(String(data).replace(",", "."));
                if (isNaN(number)) return data;
    
                const colorClass = number > 0 ? 'text-success' : (number < 0 ? 'text-danger' : '');
                let formattedNumber = number.toLocaleString(locale, options);
                if (isPercent) formattedNumber += '%';
                
                return `<span class="fw-bold ${colorClass}">${formattedNumber}</span>`;
            }
            return data;
        };
    }, // <--- ¡AQUÍ FALTABA UNA COMA!

    renderTable(stocks, timestamp, visibleColumns, columnConfig) {
        console.log(`[UI] Renderizando tabla principal con ${stocks.length} acciones.`);
        if (this.dataTable) {
            this.dataTable.destroy();
            $(this.dom.stocksTable).empty();
        }

        if (!stocks || stocks.length === 0) {
            this.updateStatus('No hay datos para mostrar con el filtro actual.', 'warning');
            return;
        }

        const allHeadings = Object.keys(stocks[0]);
        let headingsToRender = visibleColumns.filter(h => allHeadings.includes(h));
        
        if (headingsToRender.length === 0 && allHeadings.length > 0) {
            headingsToRender = allHeadings;
        }

        const dtColumns = headingsToRender.map(key => ({
            data: key,
            title: (columnConfig[key] && columnConfig[key].title) || key.replace(/_/g, ' '),
            render: (columnConfig[key] && columnConfig[key].render) || null
        }));
        
        this.dataTable = $(this.dom.stocksTable).DataTable({
            data: stocks,
            columns: dtColumns,
            responsive: true,
            language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
            dom: 'Bfrtip',
            buttons: ['excelHtml5', 'csvHtml5'],
            order: []
        });

        this.updateStatus(`Mostrando ${stocks.length} acciones. Fuente: database`, 'success');
        if (this.dom.lastUpdate) {
            this.dom.lastUpdate.innerHTML = `<i class="fas fa-clock me-1"></i>Última act: ${timestamp}`;
        }
    }
};