// src/static/js/managers/uiManager.js

export default class UIManager {
    constructor(app) {
        this.app = app;
        this.dataTables = {}; // Almacena instancias de DataTables por ID de tabla
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.loadingMessage = document.getElementById('loadingMessage');
    }

    getContainer(widgetId) {
        // Devuelve el elemento contenedor del widget, que es el que tiene el ID y la clase 'grid-stack-item'.
        return document.getElementById(widgetId);
    }

    initialize() {
        // Lógica de inicialización general de UI que no depende de un widget específico.
        console.log('[UIManager] Inicializado y listo.');
    }

    initializeWidget() {
        // El constructor ya ha hecho el trabajo principal.
        // Este método se podría usar para lógica que depende del DOM listo,
        // pero por ahora lo mantenemos simple.
        console.log('[UIManager] Inicializado y listo.');
    }

    renderTable(tableId, data, columns, extraOptions = {}) {
        console.log(`[UI] Renderizando tabla '${tableId}'. Datos recibidos:`, data);

        // Guarda de seguridad: verificar que DataTables se ha cargado.
        if (!$.fn.dataTable) {
            console.error("[UI] La librería DataTables ($.fn.dataTable) no está disponible. Asegúrate de que los scripts del CDN se hayan cargado correctamente. Abortando renderizado de la tabla.");
            this.app.uiManager.updateStatus('Error: No se pudo cargar la librería de tablas.', 'danger');
            return;
        }

        const tableElement = document.getElementById(tableId);
        if (!tableElement) {
            console.warn(`[UI] Se intentó renderizar la tabla '${tableId}', pero el elemento no se encontró en el DOM. Abortando para evitar errores.`);
            return;
        }

        try {
            if ($.fn.dataTable.isDataTable(`#${tableId}`)) {
                const dt = $(`#${tableId}`).DataTable();
                dt.clear();
                dt.rows.add(data);
                dt.columns.adjust().draw();
            } else {
                const dtConfig = {
                    data: data,
                    columns: columns,
                    responsive: true,
                    autoWidth: false,
                    processing: false,
                    language: this.getDataTablesLang(),
                    dom: 'Bfrtip',
                    buttons: ['excel', 'csv'],
                    order: [[2, 'desc']], // Asumiendo que la 3ª columna es siempre un buen criterio
                    ...extraOptions
                };

                $(tableElement).DataTable(dtConfig);
            }
            console.log(`[UI] DataTables para '${tableId}' inicializado.`);
            
        } catch (error) {
            console.error(`[UI] Error al renderizar DataTables para '${tableId}':`, error);
            // Opcional: mostrar un mensaje de error en la UI
        }
    }

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
    }
    
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
    }
    
    updateStatus(message, type) {
        const statusMessage = document.getElementById('statusMessage');
        if (!statusMessage) return;
        statusMessage.className = `alert alert-${type} small py-2`;
        statusMessage.innerHTML = `<i class="fas fa-info-circle me-1"></i> ${message}`;
    }

    updateLastUpdateTimestamp(timestamp) {
        const lastUpdate = document.getElementById('lastUpdate');
        if(!lastUpdate) return;
        lastUpdate.innerHTML = `<i class="fas fa-clock me-1"></i>Última act: ${timestamp}`;
    }

    updateRefreshButton(html, isDisabled, clickHandler) {
        const refreshBtn = document.getElementById('refreshBtn');
        if (!refreshBtn) return;
        refreshBtn.innerHTML = html;
        refreshBtn.disabled = isDisabled;
        // Reasignar el handler para asegurar que siempre sea el último
        refreshBtn.onclick = clickHandler;
    }
    
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
    }

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
    }

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
    
    showWidget(widgetId, addToLayout = false) {
        const widgetElement = document.getElementById(widgetId);
        if (widgetElement) {
            widgetElement.style.display = ''; // O 'block', 'flex', etc., según el layout
            // Si addToLayout es true, notificamos a dashboardLayout para que lo añada al grid.
            if (addToLayout && this.app.dashboardLayout) {
                this.app.dashboardLayout.addWidget(widgetId);
            }
        } else {
            console.warn(`[UI] showWidget: No se encontró el widget con id '${widgetId}'.`);
        }
    }

    showFeedback(type, message) {
        // Implementación de ejemplo: podrías usar una librería de "toasts" o notificaciones.
        console.log(`[UI Feedback] ${type.toUpperCase()}: ${message}`);
        
        // Aquí podrías añadir una lógica para mostrar un toast o un alert temporal.
        // Por ahora, lo dejamos en la consola para evitar dependencias adicionales.
        const feedbackEl = document.createElement('div');
        feedbackEl.className = `alert alert-${type} position-fixed bottom-0 end-0 m-3`;
        feedbackEl.style.zIndex = "1050"; // Asegurar que esté por encima de otros elementos
        feedbackEl.textContent = message;
        document.body.appendChild(feedbackEl);

        setTimeout(() => {
            feedbackEl.remove();
        }, 3000);
    }
}