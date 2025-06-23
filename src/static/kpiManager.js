// src/static/js/kpiManager.js

window.kpiManager = {
    dataTable: null,
    dom: {},
    socket: null,
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
            updateBtn: document.getElementById('updateKPIsBtn'),
            table: document.getElementById('kpiTable'),
            alert: document.getElementById('kpiUpdateAlert'),
            selectStocksBtn: document.getElementById('selectKPIStocksBtn'),
            selectionModal: document.getElementById('kpiSelectionModal'),
            selectionForm: document.getElementById('kpiSelectionForm'),
            saveSelectionBtn: document.getElementById('saveKPISelectionBtn'),
            stockSearchInput: document.getElementById('kpiStockSearch'),
            columnBtn: document.getElementById('kpiColumnBtn'),
            columnModal: document.getElementById('kpiColumnConfigModal'),
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
            const label = this.columnConfig[colKey]?.title || colKey;
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

        bootstrap.Modal.getInstance(this.dom.columnModal).hide();
        this.renderTable(this.dataTable.rows().data().toArray());
    },

    renderTable(data) {
        if (this.dataTable) {
            this.dataTable.destroy();
        }
        $(this.dom.table).empty();

        const columns = this.columnPrefs.visible.map(key => {
            const config = this.columnConfig[key] || {};
            const titleWithTooltip = `
                <span data-bs-toggle="tooltip" data-bs-placement="top" title="${config.description || ''}">
                    ${config.title || key}
                    <i class="fas fa-info-circle fa-xs text-muted ms-1"></i>
                </span>`;
            
            return {
                data: key,
                title: titleWithTooltip,
                render: config.render,
                defaultContent: config.defaultContent || ''
            };
        });

        this.dataTable = $(this.dom.table).DataTable({
            data,
            columns,
            order: [[0, 'asc']],
            responsive: true,
            language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
            dom: 'Bfrtip',
            buttons: ['excelHtml5', 'csvHtml5'],
            "drawCallback": function( settings ) {
                const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.map(function (tooltipTriggerEl) {
                    if (!bootstrap.Tooltip.getInstance(tooltipTriggerEl)) {
                        return new bootstrap.Tooltip(tooltipTriggerEl, { html: true, trigger: 'hover' });
                    }
                });
            }
        });
    },
    
    async openSelectionModal() {
        try {
            this.dom.selectionForm.innerHTML = '<div class="text-center"><span class="spinner-border"></span></div>';
            const response = await fetch('/api/kpis/selection');
            const stocks = await response.json();
            this.dom.selectionForm.innerHTML = '';
            stocks.forEach(stock => {
                this.dom.selectionForm.innerHTML += `
                    <div class="col-4 stock-checkbox-item">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" value="${stock.nemo}" id="check-${stock.nemo}" ${stock.is_selected ? 'checked' : ''}>
                            <label class="form-check-label" for="check-${stock.nemo}">${stock.nemo}</label>
                        </div>
                    </div>
                `;
            });
        } catch (error) {
            console.error("Error al cargar la selección de acciones:", error);
            this.dom.selectionForm.innerHTML = '<div class="alert alert-danger">No se pudieron cargar las acciones.</div>';
        }
    },

    filterStockSelection() {
        const filter = this.dom.stockSearchInput.value.toUpperCase();
        const items = this.dom.selectionForm.querySelectorAll('.stock-checkbox-item');
        items.forEach(item => {
            const label = item.querySelector('label').textContent.toUpperCase();
            item.style.display = label.includes(filter) ? '' : 'none';
        });
    },

    async handleSaveSelection() {
        const selectedNemos = Array.from(this.dom.selectionForm.querySelectorAll('input:checked')).map(input => input.value);
        
        this.showAlert('Guardando selección...', 'info', false);
        try {
            const response = await fetch('/api/kpis/selection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nemos: selectedNemos })
            });
            if (!response.ok) throw new Error('No se pudo guardar la selección.');
            
            bootstrap.Modal.getInstance(this.dom.selectionModal).hide();
            this.showAlert('¡Selección guardada! La tabla se actualizará.', 'success');
            this.loadKpis();
        } catch (error) {
            this.showAlert(error.message, 'danger');
        }
    },
    
    async handleUpdateClick() {
        this.dom.updateBtn.disabled = true;
        this.dom.updateBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Actualizando...';
        this.showAlert('Iniciando proceso de actualización con IA. Esto puede tardar varios minutos...', 'info', false);
        
        try {
            const response = await fetch('/api/kpis/update', { method: 'POST' });
            if (response.status !== 202) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'El servidor no pudo iniciar el proceso.');
            }
        } catch (error) {
            this.showAlert(error.message, 'danger');
            this.dom.updateBtn.disabled = false;
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Cargar/Actualizar KPIs';
        }
    },

    showAlert(message, type = 'info', autoHide = true) {
        const alertEl = this.dom.alert;
        alertEl.className = `alert alert-${type}`;
        alertEl.innerHTML = message;
        alertEl.classList.remove('d-none');

        if(autoHide) {
            setTimeout(() => {
                alertEl.classList.add('d-none');
            }, 5000);
        }
    }
};