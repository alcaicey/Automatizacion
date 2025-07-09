// src/static/uiManager.modular.js
// Este archivo es una copia de uiManager.js, pero refactorizado para ser un módulo ES.
// El único cambio es la palabra clave `export`.

export const uiManager = {
    app: null, // Referencia a la instancia principal de la App

    init(appInstance) {
        this.app = appInstance;
        console.log('[UI] Módulo inicializado.');
    },

    renderTable(data, tableId, columns, buttons = ['excel', 'csv']) {
        console.log(`[UI] Renderizando tabla '${tableId}'. Datos recibidos:`, JSON.stringify(data, null, 2));

        const tableElement = document.getElementById(tableId);
        if (!tableElement) {
            console.warn(`[UI] Elemento de tabla con ID '${tableId}' no encontrado. Se omite el renderizado.`);
            return;
        }

        try {
            if ($.fn.DataTable.isDataTable(tableElement)) {
                $(tableElement).DataTable().destroy();
            }

            const dtConfig = {
                data: data,
                columns: columns,
                responsive: true,
                autoWidth: false,
                processing: false,
                language: this.getDataTablesLang(),
                dom: 'Bfrtip',
                buttons: buttons,
                order: [[2, 'desc']] // Asumiendo que la 3ª columna es siempre un buen criterio
            };

            $(tableElement).DataTable(dtConfig);
            console.log(`[UI] DataTables para '${tableId}' inicializado.`);
            
        } catch (error) {
            console.error(`[UI] Error al renderizar DataTables para '${tableId}':`, error);
            // Opcional: mostrar un mensaje de error en la UI
        }
    },

    renderColumnModal(allColumns, visibleColumns, columnConfig, formId) {
        const columnConfigForm = document.getElementById(formId);
        if (!columnConfigForm) {
            console.warn(`[UI] Formulario de configuración de columnas con ID '${formId}' no encontrado.`);
            return;
        }
        columnConfigForm.innerHTML = allColumns.map(col => `
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
        const statusMessage = document.getElementById('statusMessage');
        if (!statusMessage) return;
        statusMessage.className = `alert alert-${type} small py-2`;
        statusMessage.innerHTML = `<i class="fas fa-info-circle me-1"></i> ${message}`;
    },

    updateLastUpdateTimestamp(timestamp) {
        const lastUpdate = document.getElementById('lastUpdate');
        if(!lastUpdate) return;
        lastUpdate.innerHTML = `<i class="fas fa-clock me-1"></i>Última act: ${timestamp}`;
    },

    updateRefreshButton(html, isDisabled, clickHandler) {
        const refreshBtn = document.getElementById('refreshBtn');
        if (!refreshBtn) return;
        refreshBtn.innerHTML = html;
        refreshBtn.disabled = isDisabled;
        // Reasignar el handler para asegurar que siempre sea el último
        refreshBtn.onclick = clickHandler;
    },
    
    toggleLoading(show, message = 'Cargando...') {
        console.log(`[UI] toggleLoading llamado con show=${show}, message="${message}"`);
        const loadingOverlay = document.getElementById('loading-overlay');
        const loadingMessage = document.getElementById('loadingMessage');
        
        if(!loadingOverlay || !loadingMessage) {
            console.error('[UI] No se encontró el elemento loadingOverlay o loadingMessage en el DOM.');
            return;
        }
        loadingMessage.textContent = message;
        loadingOverlay.style.display = show ? 'flex' : 'none';
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
    },

    updatePortfolioSummary(summary) {
        if (!summary) return;

        const formatCurrency = (val) => new Intl.NumberFormat('es-CL', { 
            style: 'currency', currency: 'CLP', minimumFractionDigits: 0 
        }).format(val || 0);

        document.getElementById('totalPaid').textContent = formatCurrency(summary.total_paid);
        document.getElementById('totalCurrentValue').textContent = formatCurrency(summary.total_current_value);
        
        const totalGainLossEl = document.getElementById('totalGainLoss');
        if (totalGainLossEl) {
            totalGainLossEl.textContent = formatCurrency(summary.total_gain_loss);
            totalGainLossEl.className = (summary.total_gain_loss || 0) >= 0 ? 'h5 mb-0 text-success' : 'h5 mb-0 text-danger';
        }
    }
}; 