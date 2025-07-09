// src/static/js/managers/dividendManager.js

export default class DividendManager {
    constructor(app) {
        this.app = app;
        this.dataTable = null;
        this.dom = {};
        this.isInitialLoad = true;
        this.columnPrefs = {
            all: [],
            visible: [],
        };
        this.columnConfig = {
            'symbol': { title: 'Nemo', data: 'symbol' },
            'name': { title: 'Nombre', data: 'name' },
            'record_date': { title: 'Fecha Límite', data: 'record_date' },
            'ex_dividend_date': { title: 'Fecha Ex-Div', data: 'ex_dividend_date' },
            'payment_date': { title: 'Fecha Pago', data: 'payment_date' },
            'dividend_rate': { title: 'Monto Div.', data: 'dividend_rate', render: (d, t, r) => d ? `${r.currency} ${d.toLocaleString('es-CL')}` : 'N/A' },
            'dividend_yield_on_price': { title: 'Yield s/Precio', data: 'dividend_yield_on_price', render: (d) => d ? `${d.toFixed(2)}%` : 'N/A' },
            'pre_ex_vc': { title: 'Precio Ex-Div', data: 'ex_dividend_price', render: (d, t, r) => d ? `${r.currency} ${d.toLocaleString('es-CL')}` : 'N/A' },
        };
        this.socket = null;
        this.uiManager = app.uiManager; // Asignar desde la app
    }

    initializeWidget(container) {
        if (!container) {
            console.warn('[DividendManager] Contenedor del widget no definido. Cancelando inicialización.');
            return;
        }
        this.dom = {
            table: document.getElementById('dividendTable'),
            loadingOverlay: document.getElementById('loadingOverlayDividends'),
            columnModal: document.getElementById('dividendColumnConfigModal'),
            columnForm: document.getElementById('dividendColumnConfigForm'),
            savePrefsBtn: document.getElementById('saveDividendColumnPrefs'),
            updateBtn: document.getElementById('updateDividendsBtn'),
            alertContainer: document.getElementById('dividend-alert-container'),
            textFilter: document.getElementById('dividendTextFilter'),
            dateFromFilter: document.getElementById('dividendDateFrom'),
            dateToFilter: document.getElementById('dividendDateTo'),
            columnFilter: document.getElementById('dividendColumnFilter'),
            applyFiltersBtn: document.getElementById('applyDividendFiltersBtn'),
            clearFiltersBtn: document.getElementById('clearDividendFiltersBtn'),
        };
        if (!this.dom.table) return;

        this.attachEventListeners();
        this.loadInitialData();
    }

    async loadInitialData() {
        await this.loadPreferences();
        await this.loadDividends();
    }

    attachEventListeners() {
        this.dom.updateBtn.addEventListener('click', () => this.handleUpdateClick());
        this.dom.savePrefsBtn.addEventListener('click', () => this.handleSavePrefs());
        
        this.dom.applyFiltersBtn.addEventListener('click', () => {
            this.isInitialLoad = false;
            this.loadDividends();
        });
        this.dom.clearFiltersBtn.addEventListener('click', () => this.clearCustomFilters());

        this.socket.on('dividend_update_complete', (result) => {
            console.log('[DividendManager] Actualización completada:', result);
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Revisar';
            this.dom.updateBtn.disabled = false;
            
            this.displayChanges(result);
            if (!result.error) {
                this.loadDividends();
            }
        });
    }

    async loadPreferences() {
        try {
            const data = await this.app.fetchData('/api/dividends/columns');
            this.columnPrefs.all = data.all_columns;
            this.columnPrefs.visible = data.visible_columns;
            this.renderColumnModal();
            this.populateColumnFilterDropdown();
        } catch (error) {
            console.error('[DividendManager] Error al cargar preferencias de columnas:', error);
            this.showFeedback(`Error al cargar configuración: ${error.message}`, 'danger');
        }
    }

    async loadDividends() {
        if (this.isInitialLoad) {
            this.setDefaultFilters();
        }

        const params = new URLSearchParams();
        const startDate = this.dom.dateFromFilter.value;
        const endDate = this.dom.dateToFilter.value;
        const columnFilter = this.dom.columnFilter.value;
        const textFilter = this.dom.textFilter.value.trim();

        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        if (columnFilter === 'is_ipsa') {
            if (textFilter === 'true') {
                 params.append('is_ipsa', 'true');
            }
        } else if (textFilter) {
            params.append('search_text', textFilter);
            if (columnFilter) {
                params.append('search_column', columnFilter);
            }
        }

        this.showFeedback('Cargando dividendos...', 'info', true);

        try {
            const dividends = await this.app.fetchData(`/api/dividends?${params.toString()}`);
            this.renderTable(dividends);
            this.showFeedback(`Mostrando ${dividends.length} dividendos.`, 'success');
        } catch (error) {
            console.error('Error al cargar dividendos:', error);
            this.renderTable([]); // Renderizar tabla vacía en caso de error
            this.showFeedback(`Error al cargar dividendos: ${error.message}`, 'danger');
        }
    }
    
    populateColumnFilterDropdown() {
        const currentVal = this.dom.columnFilter.value;
        this.dom.columnFilter.innerHTML = '<option value="">Cualquier Columna</option>';
        this.dom.columnFilter.innerHTML += `<option value="is_ipsa">IPSA</option>`;
        
        this.columnPrefs.visible.forEach((colKey) => {
            if (colKey === 'is_ipsa') return;
            const title = this.columnConfig[colKey]?.title || colKey.replace(/_/g, ' ');
            this.dom.columnFilter.innerHTML += `<option value="${colKey}">${title}</option>`;
        });
        this.dom.columnFilter.value = currentVal;
    }

    showFeedback(message, type = 'info', isLoading = false) {
        if (!this.dom.alertContainer) return;
        
        const alert = this.dom.alertContainer;
        alert.className = `alert alert-${type} d-flex align-items-center`;
        
        let content = '';
        if (isLoading) {
            content += '<div class="spinner-border spinner-border-sm me-2" role="status"></div>';
        }
        content += `<span>${message}</span>`;
        
        alert.innerHTML = content;
        alert.classList.remove('d-none');
    }

    setDefaultFilters() {
        const today = new Date();
        const future = new Date();
        future.setMonth(today.getMonth() + 3);

        const formatDate = (date) => date.toISOString().split('T')[0];

        this.dom.dateFromFilter.value = formatDate(today);
        this.dom.dateToFilter.value = formatDate(future);
        this.dom.textFilter.value = 'true';
        this.dom.columnFilter.value = 'is_ipsa';
        
        this.isInitialLoad = false;
    }
    
    clearCustomFilters() {
        this.isInitialLoad = false;
        this.dom.dateFromFilter.value = '';
        this.dom.dateToFilter.value = '';
        this.dom.columnFilter.value = '';
        this.dom.textFilter.value = '';
        this.loadDividends();
    }

    renderColumnModal() {
        this.dom.columnForm.innerHTML = '';
        this.columnPrefs.all.forEach(colKey => {
            const isChecked = this.columnPrefs.visible.includes(colKey);
            const label = this.columnConfig[colKey]?.title || colKey.replace(/_/g, ' ');
            this.dom.columnForm.innerHTML += `
                <div class="col-6"><div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${colKey}" id="div-col-${colKey}" ${isChecked ? 'checked' : ''}>
                    <label class="form-check-label" for="div-col-${colKey}">${label}</label>
                </div></div>`;
        });
    }

    renderTable(data) {
        if (this.dataTable) {
            this.dataTable.destroy();
            $(this.dom.table).empty();
        }

        if (!data || data.length === 0) {
            this.dataTable = $(this.dom.table).DataTable({
                data: [],
                columns: this.columnPrefs.visible.map(key => ({ 
                    title: this.columnConfig[key]?.title || key 
                })),
                responsive: true,
                language: { 
                    url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json',
                    emptyTable: "Ningún dato disponible en esta tabla"
                },
                dom: 't',
            });
            return;
        }

        const dtColumns = this.columnPrefs.visible.map(key => ({
            data: this.columnConfig[key]?.data || key,
            title: this.columnConfig[key]?.title || key,
            render: this.columnConfig[key]?.render || null,
        }));
        
        let orderColumnIndex = this.columnPrefs.visible.indexOf('fec_pago');
        if (orderColumnIndex === -1) {
            orderColumnIndex = this.columnPrefs.visible.indexOf('limit_date');
        }
        if (orderColumnIndex === -1) {
            orderColumnIndex = 0;
        }

        this.dataTable = $(this.dom.table).DataTable({
            data,
            columns: dtColumns,
            order: [[ orderColumnIndex, 'asc' ]],
            responsive: true,
            language: { url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
            dom: 'Bfrtip',
            buttons: ['excelHtml5', 'csvHtml5'],
            initComplete: function () {
                const dtContainer = $(this.api().table().container());
                const toolbar = $('#dividends-toolbar');
                if (toolbar.length) {
                    dtContainer.find('.dt-buttons').appendTo(toolbar);
                    dtContainer.find('.dataTables_filter').appendTo(toolbar);
                    toolbar.find('.dataTables_filter input').attr('id', 'dividendsTableSearch');
                }
            }
        });
    }
    
    async handleSavePrefs() {
        this.isInitialLoad = false;
        const selected = Array.from(this.dom.columnForm.querySelectorAll('input:checked')).map(i => i.value);
        this.columnPrefs.visible = selected;
        
        await fetch('/api/dividends/columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: selected })
        });

        bootstrap.Modal.getInstance(this.dom.columnModal).hide();
        this.renderTable(this.dataTable.rows().data().toArray());
        this.populateColumnFilterDropdown();
    }

    async handleUpdateClick() {
        this.isInitialLoad = false;
        const btn = this.dom.updateBtn;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Actualizando...`;
        btn.disabled = true;
        this.dom.changesAlert.classList.add('d-none');

        try {
            const response = await fetch('/api/dividends/update', { method: 'POST' });
            if (response.status !== 202) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'El servidor no pudo iniciar el proceso.');
            }
        } catch (error) {
            this.displayChanges({ error: error.message });
            btn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Revisar';
            btn.disabled = false;
        }
    }

    displayChanges(result) {
        const alertEl = this.dom.changesAlert;
        if (result.error) {
            alertEl.className = 'alert alert-danger';
            alertEl.innerHTML = `<strong>Error:</strong> ${result.error}`;
        } else if (!result.has_changes) {
            alertEl.className = 'alert alert-info';
            alertEl.textContent = 'No se encontraron cambios. Los datos ya estaban actualizados.';
        } else {
            alertEl.className = 'alert alert-success';
            alertEl.innerHTML = `
                <strong>¡Datos actualizados!</strong>
                <ul>
                    <li><strong>Dividendos Nuevos:</strong> ${result.summary.added_count}</li>
                    <li><strong>Dividendos Eliminados:</strong> ${result.summary.removed_count}</li>
                </ul>
            `;
        }
        alertEl.classList.remove('d-none');
    }
}