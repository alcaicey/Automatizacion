// src/static/uiManager.js

const uiManager = {
    dom: {}, // El DOM específico de las tablas ya no se cachea aquí

    init() {
        // Cacheamos solo elementos globales que siempre existen en la página
        this.dom = {
            refreshBtn: document.getElementById('refreshBtn'),
            autoUpdateSelect: document.getElementById('autoUpdateSelect'),
            countdownTimer: document.getElementById('countdownTimer'),
            statusMessage: document.getElementById('statusMessage'),
            lastUpdate: document.getElementById('lastUpdate'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            loadingMessage: document.getElementById('loadingMessage'),
            // Referencias a modales y formularios que están siempre en el DOM del layout
            columnConfigModal: document.getElementById('columnConfigModal'),
            columnConfigForm: document.getElementById('columnConfigForm'),
            saveColumnPrefsBtn: document.getElementById('saveColumnPrefs')
        };
        console.log('[UI] Módulo inicializado y DOM global cacheado.');
    },

    renderTable(data, timestamp, visibleColumns, columnConfig) {
        const tableElement = document.getElementById('stocksTable');
        // Si el widget de "Datos del Mercado" no está visible, el elemento no existirá.
        // En ese caso, simplemente no hacemos nada.
        if (!tableElement) {
            console.log('[UI] Widget de tabla de acciones no encontrado. Se omite el renderizado.');
            return;
        }

        if ($.fn.DataTable.isDataTable(tableElement)) {
            $(tableElement).DataTable().destroy();
        }

        const columns = visibleColumns.map(key => ({
            data: key,
            title: columnConfig[key]?.title || key,
            render: columnConfig[key]?.render || ((d) => d === null ? '' : d)
        }));

        $(tableElement).DataTable({
            data: data,
            columns: columns,
            responsive: true,
            autoWidth: false,
            language: this.getDataTablesLang(),
            dom: 'Bfrtip',
            buttons: ['excel', 'csv'],
            order: [[2, 'desc']] // Ordenar por variación por defecto
        });
        
        // Actualizamos el estado general, que es global
        this.updateStatus(`Mostrando ${data.length} acciones. Fuente: ${timestamp}`, 'success');
    },

    renderColumnModal(allColumns, visibleColumns, columnConfig) {
        if (!this.dom.columnConfigForm) return;
        this.dom.columnConfigForm.innerHTML = allColumns.map(col => `
            <div class="col-6 col-md-4">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${col}" id="col_${col}" ${visibleColumns.includes(col) ? 'checked' : ''}>
                    <label class="form-check-label" for="col_${col}">${columnConfig[col]?.title || col}</label>
                </div>
            </div>
        `).join('');
    },
    
    renderFilterInputs(filters) {
        const stockFilterForm = document.getElementById('stockFilterForm');
        if (!stockFilterForm) return;

        const stockCodeInputs = stockFilterForm.querySelectorAll('.stock-code');
        const allStocksCheck = stockFilterForm.querySelector('#allStocksCheck');

        if(stockCodeInputs.length > 0) {
            stockCodeInputs.forEach((input, index) => {
                input.value = filters.codes[index] || '';
            });
        }
        if(allStocksCheck) {
            allStocksCheck.checked = filters.all;
        }
    },
    
    updateStatus(message, type) {
        if (!this.dom.statusMessage) return;
        this.dom.statusMessage.className = `alert alert-${type} small py-2`;
        this.dom.statusMessage.innerHTML = `<i class="fas fa-info-circle me-1"></i> ${message}`;
    },

    updateLastUpdateTimestamp(timestamp) {
        if(!this.dom.lastUpdate) return;
        this.dom.lastUpdate.innerHTML = `<i class="fas fa-clock me-1"></i>Última act: ${timestamp}`;
    },

    updateRefreshButton(html, isDisabled) {
        if (!this.dom.refreshBtn) return;
        this.dom.refreshBtn.innerHTML = html;
        this.dom.refreshBtn.disabled = isDisabled;
    },
    
    toggleLoading(show, message = 'Cargando...') {
        if(!this.dom.loadingOverlay) return;
        this.dom.loadingMessage.textContent = message;
        this.dom.loadingOverlay.classList.toggle('d-none', !show);
    },

    createNumberRenderer(isPercent = false, locale = 'es-CL', options = {}) {
        return function(data, type) {
            if (type !== 'display' || data === null || data === undefined) return data;
            const num = parseFloat(String(data).replace(",", "."));
            if (isNaN(num)) return data;
            
            let finalOptions = options;
            if (isPercent) {
                finalOptions = { style: 'decimal', minimumFractionDigits: 2, maximumFractionDigits: 2, ...options };
            }
            
            let formatted = new Intl.NumberFormat(locale, finalOptions).format(num);

            if (isPercent) {
                const color = num > 0 ? 'text-success' : num < 0 ? 'text-danger' : 'text-muted';
                return `<span class="fw-bold ${color}">${formatted} %</span>`;
            }
            return formatted;
        };
    },

    getDataTablesLang() {
        return {
            "search": "Buscar:",
            "lengthMenu": "Mostrar _MENU_ registros",
            "info": "Mostrando _START_ a _END_ de _TOTAL_ registros",
            "infoEmpty": "Mostrando 0 a 0 de 0 registros",
            "infoFiltered": "(filtrado de _MAX_ registros totales)",
            "zeroRecords": "No se encontraron registros coincidentes",
            "paginate": { "first": "Primero", "last": "Último", "next": "Siguiente", "previous": "Anterior" }
        };
    }
};