// src/static/js/kpiManager.js

window.kpiManager = {
    dataTable: null,
    dom: {},
    socket: null,
    updateTimeout: null,
    columnPrefs: {
        all: [],
        visible: [],
    },
    columnConfig: {
        'nemo': { title: 'Empresa', description: 'Nemotécnico de la acción.' },
        'precio_cierre_ant': { title: 'Precio', description: 'Último precio de cierre registrado.', render: (d) => d ? d.toLocaleString('es-CL', { style: 'currency', currency: 'CLP' }) : 'N/A' },
        'razon_pre_uti': { title: 'P/E', description: 'Ratio Precio/Utilidad (Price-to-Earnings). Mide cuántas veces se está pagando el beneficio del último año.', defaultContent: '<i>N/A</i>' },
        'roe': { title: 'ROE (%)', description: 'Retorno sobre el Patrimonio (Return on Equity). Mide la rentabilidad generada sobre el capital de los accionistas.', defaultContent: '<i>N/A</i>' },
        'dividend_yield': { title: 'Yield (%)', description: 'Rentabilidad por dividendo. Es el dividendo anual por acción dividido por el precio de la acción.', defaultContent: '<i>N/A</i>' },
        'riesgo': { 
            title: 'Riesgo/Consenso',
            description: 'Consenso de recomendación de analistas (obtenido por IA).',
            defaultContent: '<i>N/A</i>',
            render: function(data) {
                if (!data || data === 'N/A') return '<i>N/A</i>';
                const classes = {
                    'Comprar': 'bg-success text-white',
                    'Mantener': 'bg-warning text-dark',
                    'Vender': 'bg-danger text-white'
                };
                return `<span class="badge ${classes[data] || 'bg-secondary'}">${data}</span>`;
            }
        },
        'beta': { title: 'Beta', description: 'Medida de la volatilidad de la acción en comparación con el mercado. >1 más volátil, <1 menos volátil.', defaultContent: '<i>N/A</i>' },
        'debt_to_equity': { title: 'Deuda/Patr.', description: 'Ratio Deuda/Patrimonio. Mide el apalancamiento financiero de la empresa.', defaultContent: '<i>N/A</i>' },
        'kpi_last_updated': {
            title: 'Actualizado (IA)',
            description: 'Fecha de la última actualización de los datos obtenidos por IA.',
            defaultContent: '<i>Nunca</i>',
            render: function(data) {
                if (!data) return '<i>Nunca</i>';
                const date = new Date(data);
                return `<span title="${date.toLocaleString('es-CL')}">${date.toLocaleDateString('es-CL')}</span>`;
            }
        },
        'kpi_source': {
            title: 'Fuente (IA)',
            description: 'Fuente de datos principal reportada por la IA.',
            defaultContent: '<i>N/A</i>',
            render: function(data) {
                return data ? `<span title="${data}">${data.substring(0, 20)}${data.length > 20 ? '...' : ''}</span>` : '<i>N/A</i>';
            }
        }
    },

    init() {
        this.dom = {
            toolbar: document.getElementById('kpi-toolbar'),
            updateBtn: document.getElementById('updateKPIsBtn'),
            table: document.getElementById('kpiTable'),
            alert: document.getElementById('kpiUpdateAlert'),
            selectStocksBtn: document.getElementById('selectKPIStocksBtn'),
            selectionModal: new bootstrap.Modal(document.getElementById('kpiSelectionModal')),
            selectionForm: document.getElementById('kpiSelectionForm'),
            saveSelectionBtn: document.getElementById('saveKPISelectionBtn'),
            stockSearchInput: document.getElementById('kpiStockSearch'),
            columnBtn: document.getElementById('kpiColumnBtn'),
            columnModal: new bootstrap.Modal(document.getElementById('kpiColumnConfigModal')),
            columnForm: document.getElementById('kpiColumnConfigForm'),
            saveColumnPrefsBtn: document.getElementById('saveKPIColumnPrefs'),
        };
        if (!this.dom.table) return;

        this.socket = io();
        this.attachEventListeners();
        this.loadInitialData();
    },
    
    attachEventListeners() {
        this.dom.updateBtn.addEventListener('click', () => this.handleUpdateClick());
        this.dom.selectStocksBtn.addEventListener('click', () => this.openSelectionModal());
        this.dom.saveSelectionBtn.addEventListener('click', () => this.handleSaveSelection());
        this.dom.stockSearchInput.addEventListener('keyup', () => this.filterStockSelection());
        this.dom.saveColumnPrefsBtn.addEventListener('click', () => this.handleSavePrefs());

        this.socket.on('kpi_update_progress', (data) => {
            const message = `[${data.progress}] Procesando ${data.nemo}... (${data.status})`;
            this.showAlert(message, 'info', false);
        });
        
        this.socket.on('kpi_update_complete', (data) => {
            if (this.updateTimeout) clearTimeout(this.updateTimeout);
            this.updateTimeout = null;
            
            this.dom.updateBtn.disabled = false;
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Cargar/Actualizar KPIs';
            
            const alertType = data.error ? 'danger' : 'success';
            const alertMessage = data.error || data.message;
            this.showAlert(alertMessage, alertType);
            
            this.loadKpis();
        });
    },

    async loadInitialData() {
        await this.loadPreferences();
        await this.loadKpis();
    },

    async loadKpis() {
        try {
            // --- INICIO DE LA MODIFICACIÓN: Mostrar loading ---
            if (this.dataTable) {
                // Si la tabla ya existe, mostrar un overlay o un mensaje simple
                this.dataTable.clear().draw();
                $(this.dom.table.tBodies[0]).html('<tr><td colspan="100%" class="text-center"><div class="spinner-border spinner-border-sm" role="status"></div> Actualizando datos...</td></tr>');
            }
            // --- FIN DE LA MODIFICACIÓN ---

            const response = await fetch('/api/kpis'); 
            if (!response.ok) throw new Error('No se pudieron cargar los datos de KPIs.');
            const data = await response.json();
            this.renderTable(data);
        } catch (error) {
            console.error(error);
            this.showAlert(error.message, 'danger');
        }
    },
    
    async loadPreferences() {
        try {
            const res = await fetch('/api/kpis/columns');
            if (!res.ok) throw new Error('No se pudieron cargar las preferencias de columnas.');
            const data = await res.json();
            this.columnPrefs.all = data.all_columns;
            this.columnPrefs.visible = data.visible_columns;
            this.renderColumnModal();
        } catch (error) {
            console.error(error);
        }
    },
    
    renderColumnModal() {
        this.dom.columnForm.innerHTML = '';
        this.columnPrefs.all.forEach(colKey => {
            const isChecked = this.columnPrefs.visible.includes(colKey);
            const label = this.columnConfig[colKey]?.title || colKey.replace(/_/g, ' ');
            this.dom.columnForm.innerHTML += `
                <div class="col-6"><div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${colKey}" id="kpi-col-${colKey}" ${isChecked ? 'checked' : ''}>
                    <label class="form-check-label" for="kpi-col-${colKey}">${label}</label>
                </div></div>`;
        });
    },
    
    async handleSavePrefs() {
        const selected = Array.from(this.dom.columnForm.querySelectorAll('input:checked')).map(i => i.value);
        this.columnPrefs.visible = selected;
        
        await fetch('/api/kpis/columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: selected })
        });

        this.dom.columnModal.hide();
        this.loadKpis();
    },

    // --- INICIO DE LA MODIFICACIÓN COMPLETA ---
    renderTable(data) {
        // Manejo del caso sin datos o sin selección
        if (!data || data.length === 0) {
            if (this.dataTable) {
                this.dataTable.destroy();
                this.dataTable = null;
                $(this.dom.table).empty();
            }
            const emptyMessage = `
                <div class="alert alert-info text-center">
                    <i class="fas fa-info-circle me-2"></i>
                    No hay acciones seleccionadas para mostrar KPIs. Utilice el botón 
                    <strong><i class="fas fa-check-square me-1"></i>Seleccionar Acciones</strong>
                    para empezar.
                </div>
            `;
            this.dom.table.innerHTML = emptyMessage;
            if (this.dom.toolbar.querySelector('.dt-buttons')) this.dom.toolbar.querySelector('.dt-buttons').remove();
            if (this.dom.toolbar.querySelector('.dataTables_filter')) this.dom.toolbar.querySelector('.dataTables_filter').remove();
            return;
        }

        // Si la tabla ya está inicializada, la actualizamos de forma eficiente
        if (this.dataTable) {
            this.dataTable.clear().rows.add(data).draw();
        } else { // Si no, la inicializamos por primera vez
            const columns = this.columnPrefs.visible.map(key => ({
                data: key,
                title: this.columnConfig[key]?.title || key.replace(/_/g, ' '),
                render: this.columnConfig[key]?.render || null,
                defaultContent: this.columnConfig[key]?.defaultContent || ''
            }));
            
            this.dataTable = $(this.dom.table).DataTable({
                data: data,
                columns: columns,
                responsive: true,
                stateSave: false, // Previene el "filtrado fantasma"
                language: { url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
                dom: "<'row'<'col-sm-12 col-md-6'B><'col-sm-12 col-md-6'f>>" +
                     "<'row'<'col-sm-12'tr>>" +
                     "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
                buttons: ['excelHtml5', 'csvHtml5'],
                order: [[0, 'asc']]
            });
            
            // Mover los controles a la barra de herramientas personalizada una sola vez
            const dtContainer = $(this.dom.table).closest('.dataTables_wrapper');
            $('.dt-buttons', dtContainer).appendTo(this.dom.toolbar);
            $('.dataTables_filter', dtContainer).appendTo(this.dom.toolbar);
        }
    },
    // --- FIN DE LA MODIFICACIÓN COMPLETA ---
    
    async openSelectionModal() {
        try {
            const response = await fetch('/api/kpis/selection');
            if (!response.ok) throw new Error('No se pudieron cargar las acciones.');
            const stocks = await response.json();
            
            this.dom.selectionForm.innerHTML = '';
            stocks.forEach(stock => {
                this.dom.selectionForm.innerHTML += `
                    <div class="col-sm-4 col-md-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" value="${stock.nemo}" id="kpi-check-${stock.nemo}" ${stock.is_selected ? 'checked' : ''}>
                            <label class="form-check-label" for="kpi-check-${stock.nemo}">${stock.nemo}</label>
                        </div>
                    </div>
                `;
            });
        } catch (error) {
            this.dom.selectionForm.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
        }
    },
    
    filterStockSelection() {
        const filter = this.dom.stockSearchInput.value.toUpperCase();
        const checkboxes = this.dom.selectionForm.querySelectorAll('.form-check');
        checkboxes.forEach(div => {
            const label = div.querySelector('label');
            if (label.textContent.toUpperCase().indexOf(filter) > -1) {
                div.parentElement.style.display = "";
            } else {
                div.parentElement.style.display = "none";
            }
        });
    },
    
    async handleSaveSelection() {
        const selectedNemos = Array.from(this.dom.selectionForm.querySelectorAll('input:checked')).map(i => i.value);
        try {
            const response = await fetch('/api/kpis/selection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nemos: selectedNemos })
            });
            if (!response.ok) throw new Error('No se pudo guardar la selección.');
            
            this.dom.selectionModal.hide();
            this.showAlert('Selección guardada. Los datos se cargarán ahora.', 'success');
            this.loadKpis(); // <-- Llamada clave para recargar los datos
        } catch (error) {
            this.showAlert(error.message, 'danger');
        }
    },
    
    async handleUpdateClick() {
        if (this.updateTimeout) clearTimeout(this.updateTimeout);

        this.dom.updateBtn.disabled = true;
        this.dom.updateBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Actualizando...';
        this.showAlert('Iniciando proceso de actualización con IA. Esto puede tardar varios minutos...', 'info', false);
        
        try {
            const response = await fetch('/api/kpis/update', { method: 'POST' });
            if (response.status !== 202) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'El servidor no pudo iniciar el proceso.');
            }
            
            this.updateTimeout = setTimeout(() => {
                this.showAlert('La actualización está tardando demasiado. El servidor podría haberse reiniciado. Por favor, refresca la página e intenta de nuevo.', 'warning');
                this.dom.updateBtn.disabled = false;
                this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Cargar/Actualizar KPIs con IA';
            }, 300000);

        } catch (error) {
            this.showAlert(error.message, 'danger');
            this.dom.updateBtn.disabled = false;
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Cargar/Actualizar KPIs con IA';
        }
    },

    showAlert(message, type = 'info', autoHide = true) {
        const alertEl = this.dom.alert;
        alertEl.className = `alert alert-${type}`;
        alertEl.innerHTML = message;
        alertEl.classList.remove('d-none');

        if(autoHide) {
            setTimeout(() => {
                if(alertEl) alertEl.classList.add('d-none');
            }, 5000);
        }
    }
};