// src/static/js/dividendManager.js

window.dividendManager = {
    dataTable: null,
    dom: {},
    isInitialLoad: true, // <-- NUEVA PROPIEDAD
    columnPrefs: {
        all: [],
        visible: [],
        config: {
            'nemo': { title: 'Símbolo' },
            'is_ipsa': { 
                title: 'IPSA', 
                render: (data) => data ? '<i class="fas fa-check-circle text-primary"></i>' : '' 
            },
            'descrip_vc': { title: 'Descripción' },
            'fec_lim': { title: 'Fecha Límite', render: (d) => new Date(d + 'T00:00:00Z').toLocaleDateString('es-CL', { timeZone: 'UTC' }) },
            'fec_pago': { title: 'Fecha Pago', render: (d) => new Date(d + 'T00:00:00Z').toLocaleDateString('es-CL', { timeZone: 'UTC' }) },
            'moneda': { title: 'Moneda' },
            'val_acc': { title: 'Valor', render: (d,t,r) => `${r.moneda} ${d.toLocaleString('es-CL', {minimumFractionDigits: 2, maximumFractionDigits: 4})}` },
            'num_acc_ant': { title: 'Acc. Antiguas', render: (d) => d ? d.toLocaleString('es-CL') : 'N/A' },
            'num_acc_der': { title: 'Acc. con Derecho', render: (d) => d ? d.toLocaleString('es-CL') : 'N/A' },
            'num_acc_nue': { title: 'Acc. Nuevas', render: (d) => d ? d.toLocaleString('es-CL') : 'N/A' },
            'pre_ant_vc': { title: 'Precio Antiguo', render: (d,t,r) => d ? `${r.moneda} ${d.toLocaleString('es-CL')}`: 'N/A' },
            'pre_ex_vc': { title: 'Precio Ex-Div', render: (d,t,r) => d ? `${r.moneda} ${d.toLocaleString('es-CL')}`: 'N/A' },
        }
    },
    socket: null,

    init() {
        this.dom = {
            updateBtn: document.getElementById('updateDividendsBtn'),
            table: document.getElementById('dividendsTable'),
            changesAlert: document.getElementById('dividendChangesAlert'),
            columnBtn: document.getElementById('dividendColumnBtn'),
            columnModal: document.getElementById('dividendColumnConfigModal'),
            columnForm: document.getElementById('dividendColumnConfigForm'),
            saveColumnPrefsBtn: document.getElementById('saveDividendColumnPrefs'),
            startDate: document.getElementById('dividendStartDate'),
            endDate: document.getElementById('dividendEndDate'),
            columnFilter: document.getElementById('dividendColumnFilter'),
            textFilter: document.getElementById('dividendTextFilter'),
            applyFiltersBtn: document.getElementById('applyDividendFilters'),
            clearFiltersBtn: document.getElementById('clearDividendFilters'),
        };

        if (!this.dom.table) return;

        this.socket = io();
        this.attachEventListeners();
        this.loadInitialData();
    },

    async loadInitialData() {
        await this.loadPreferences();
        await this.loadDividends();
    },

    attachEventListeners() {
        this.dom.updateBtn.addEventListener('click', () => this.handleUpdateClick());
        this.dom.saveColumnPrefsBtn.addEventListener('click', () => this.handleSavePrefs());
        
        this.dom.applyFiltersBtn.addEventListener('click', () => {
            this.isInitialLoad = false; // El usuario aplicó filtros manualmente
            this.applyCustomFilters();
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
    },

    async loadPreferences() {
        try {
            const res = await fetch('/api/dividends/columns');
            if (!res.ok) throw new Error('No se pudieron cargar las preferencias de columnas.');
            const data = await res.json();
            this.columnPrefs.all = data.all_columns;
            this.columnPrefs.visible = data.visible_columns;
            this.renderColumnModal();
            this.populateColumnFilterDropdown();
        } catch (error) {
            console.error(error);
        }
    },

    async loadDividends() {
        try {
            const response = await fetch('/api/dividends');
            if (!response.ok) throw new Error('No se pudieron cargar los dividendos.');
            const dividends = await response.json();
            this.renderTable(dividends);
            // --- INICIO DE LA MODIFICACIÓN: Aplicar filtros después de cargar ---
            this.applyCustomFilters(); 
            // --- FIN DE LA MODIFICACIÓN ---
        } catch (error) {
            console.error('Error al cargar dividendos:', error);
            this.dom.table.innerHTML = `<tr><td colspan="5" class="text-danger text-center">${error.message}</td></tr>`;
        }
    },
    
    populateColumnFilterDropdown() {
        this.dom.columnFilter.innerHTML = '<option value="">Cualquier Columna</option>';
        this.columnPrefs.visible.forEach((colKey, index) => {
            const title = this.columnPrefs.config[colKey]?.title || colKey.replace(/_/g, ' ');
            this.dom.columnFilter.innerHTML += `<option value="${index}">${title}</option>`;
        });
    },

    applyCustomFilters() {
        if (!this.dataTable) return;

        // --- INICIO DE LA MODIFICACIÓN: Lógica de filtros por defecto ---
        if (this.isInitialLoad) {
            const today = new Date();
            const future = new Date();
            future.setMonth(today.getMonth() + 3);

            // Función para formatear la fecha a YYYY-MM-DD
            const formatDate = (date) => date.toISOString().split('T')[0];

            this.dom.startDate.value = formatDate(today);
            this.dom.endDate.value = formatDate(future);
            this.dom.textFilter.value = 'true';
            
            // Encuentra el índice de la columna IPSA
            const ipsaColIndex = this.columnPrefs.visible.indexOf('is_ipsa');
            if (ipsaColIndex !== -1) {
                this.dom.columnFilter.value = ipsaColIndex;
            }
        }
        // --- FIN DE LA MODIFICACIÓN ---

        const startDate = this.dom.startDate.value ? new Date(this.dom.startDate.value + 'T00:00:00Z') : null;
        const endDate = this.dom.endDate.value ? new Date(this.dom.endDate.value + 'T23:59:59Z') : null;
        let colIndex = this.dom.columnFilter.value; // Se usa 'let' para poder modificarlo
        const searchText = this.dom.textFilter.value.trim().toLowerCase();
        
        $.fn.dataTable.ext.search.pop();

        $.fn.dataTable.ext.search.push(
            (settings, data, dataIndex) => {
                const rowData = this.dataTable.row(dataIndex).data();
                
                // 1. Filtro de Fecha
                const dateColKey = 'fec_pago';
                const dateColIndex = this.columnPrefs.visible.indexOf(dateColKey);
                if ((startDate || endDate) && dateColIndex > -1) {
                    const cellDateStr = rowData[dateColKey];
                    if (!cellDateStr) return false;
                    const cellDate = new Date(cellDateStr + 'T00:00:00Z');
                    if ((startDate && cellDate < startDate) || (endDate && cellDate > endDate)) {
                        return false;
                    }
                }

                // 2. Filtro de Texto
                if (searchText) {
                    if (colIndex) { // Búsqueda en columna específica
                        const columnKey = this.columnPrefs.visible[colIndex];
                        const cellValue = rowData[columnKey];
                        if (String(cellValue).toLowerCase().indexOf(searchText) === -1) {
                            return false;
                        }
                    } else { // Búsqueda en todas las columnas
                        let matchFound = false;
                        for (const key of this.columnPrefs.visible) {
                            const cellValue = rowData[key];
                            if (cellValue !== null && String(cellValue).toLowerCase().indexOf(searchText) !== -1) {
                                matchFound = true;
                                break;
                            }
                        }
                        if (!matchFound) return false;
                    }
                }
                return true;
            }
        );
        this.dataTable.draw();
    },
    
    clearCustomFilters() {
        this.isInitialLoad = false; // El usuario limpió los filtros
        this.dom.startDate.value = '';
        this.dom.endDate.value = '';
        this.dom.columnFilter.value = '';
        this.dom.textFilter.value = '';
        
        $.fn.dataTable.ext.search.pop();
        this.dataTable.draw();
    },

    renderColumnModal() {
        this.dom.columnForm.innerHTML = '';
        this.columnPrefs.all.forEach(colKey => {
            const isChecked = this.columnPrefs.visible.includes(colKey);
            const label = this.columnPrefs.config[colKey]?.title || colKey.replace(/_/g, ' ');
            this.dom.columnForm.innerHTML += `
                <div class="col-6"><div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${colKey}" id="div-col-${colKey}" ${isChecked ? 'checked' : ''}>
                    <label class="form-check-label" for="div-col-${colKey}">${label}</label>
                </div></div>`;
        });
    },

    renderTable(data) {
        if (this.dataTable) this.dataTable.destroy();
        $(this.dom.table).empty();

        const dtColumns = this.columnPrefs.visible.map(key => ({
            data: key,
            title: this.columnPrefs.config[key]?.title || key,
            render: this.columnPrefs.config[key]?.render || null,
        }));
        
        this.dataTable = $(this.dom.table).DataTable({
            data,
            columns: dtColumns,
            order: [[ this.columnPrefs.visible.indexOf('fec_pago') || 1, 'asc' ]],
            responsive: true,
            language: { url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
            dom: 'Bfrtip',
            buttons: ['excelHtml5', 'csvHtml5'],
        });
    },
    
    async handleSavePrefs() {
        this.isInitialLoad = false; // El usuario guardó preferencias
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
    },

    async handleUpdateClick() {
        this.isInitialLoad = false; // El usuario pidió actualizar
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
    },

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
};