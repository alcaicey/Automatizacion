// src/static/js/kpiManager.modular.js

const kpiManager = {
    // Estado encapsulado del módulo
    dataTable: null,
    dom: {},
    socket: null,
    updateTimeout: null,
    columnPrefs: {
        all: [],
        visible: [],
    },

    // Configuración de columnas
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

    init(mockSocket, mockBootstrap) {
        this.dom = {
            toolbar: document.getElementById('kpi-toolbar'),
            updateBtn: document.getElementById('updateKPIsBtn'),
            table: document.getElementById('kpiTable'),
            alert: document.getElementById('kpiUpdateAlert'),
            selectStocksBtn: document.getElementById('selectKPIStocksBtn'),
            selectionModal: mockBootstrap ? new mockBootstrap.Modal(document.getElementById('kpiSelectionModal')) : null,
            selectionForm: document.getElementById('kpiSelectionForm'),
            saveSelectionBtn: document.getElementById('saveKPISelectionBtn'),
            stockSearchInput: document.getElementById('kpiStockSearch'),
            columnBtn: document.getElementById('kpiColumnBtn'),
            columnModal: mockBootstrap ? new mockBootstrap.Modal(document.getElementById('kpiColumnConfigModal')) : null,
            columnForm: document.getElementById('kpiColumnConfigForm'),
            saveColumnPrefsBtn: document.getElementById('saveKPIColumnPrefs'),
            promptBtn: document.getElementById('kpiPromptBtn'),
            promptModal: mockBootstrap ? new mockBootstrap.Modal(document.getElementById('kpiPromptModal')) : null,
            promptTextarea: document.getElementById('kpiPromptTextarea'),
            savePromptBtn: document.getElementById('saveKpiPromptBtn'),
            promptUpdateAlert: document.getElementById('promptUpdateAlert'),
        };
        if (!this.dom.table) return;

        this.socket = mockSocket || io();
        this.attachEventListeners();
        this.initPromptEditor();
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

        this.initTooltips();
    },

    initTooltips(mockBootstrap) {
        const tooltipTriggerList = [].slice.call(this.dom.table.querySelectorAll('[title]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            if (mockBootstrap || window.bootstrap) {
                return new (mockBootstrap || window.bootstrap).Tooltip(tooltipTriggerEl);
            }
            return null;
        });
    },

    initPromptEditor() {
        this.dom.promptBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/kpi-prompt');
                if (!response.ok) throw new Error('No se pudo cargar el prompt.');
                const data = await response.json();
                this.dom.promptTextarea.value = data.prompt;
                this.dom.promptUpdateAlert.classList.add('d-none');
            } catch (error) {
                this.showAlertInPrompt(error.message, 'danger');
            }
        });

        this.dom.savePromptBtn.addEventListener('click', async () => {
            const newPrompt = this.dom.promptTextarea.value;
            try {
                const response = await fetch('/api/kpi-prompt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: newPrompt })
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Error al guardar el prompt.');
                }
                this.showAlertInPrompt('Prompt guardado con éxito.', 'success');
            } catch (error) {
                this.showAlertInPrompt(error.message, 'danger');
            }
        });
    },

    showAlertInPrompt(message, type) {
        const alertEl = this.dom.promptUpdateAlert;
        alertEl.className = `alert alert-${type}`;
        alertEl.textContent = message;
        alertEl.classList.remove('d-none');
        setTimeout(() => alertEl.classList.add('d-none'), 4000);
    },

    async loadInitialData() {
        await this.loadPreferences();
        await this.loadKpis();
    },

    async loadKpis() {
        try {
            if (this.dataTable) {
                this.dataTable.clear().draw();
            }

            const response = await fetch('/api/kpis'); 
            if (!response.ok) throw new Error('No se pudieron cargar los datos de KPIs.');
            const data = await response.json();
            this.renderTable(data);
        } catch (error) {
            console.error(error);
            const userFriendlyError = 'No se pudieron cargar los datos de KPIs.';
            this.showAlert(userFriendlyError, 'danger');
            // Lanzar siempre un error estandarizado para que el llamador no dependa del mensaje de la red
            throw new Error(userFriendlyError);
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

        if (this.dom.columnModal && typeof this.dom.columnModal.hide === 'function') {
            this.dom.columnModal.hide();
        }
        this.loadKpis();
    },

    renderTable(data) {
        if (!data || data.length === 0) {
            if (this.dataTable) {
                this.dataTable = null;
                this.dom.table.innerHTML = ''; 
            }
            this.dom.table.innerHTML = '<tbody><tr><td colspan="100%" class="text-center p-4">No hay acciones seleccionadas para mostrar KPIs.</td></tr></tbody>';
            return;
        }
    },

    async openSelectionModal() {
        try {
            const response = await fetch('/api/kpi/selection');
            if (!response.ok) throw new Error('No se pudieron cargar las selecciones.');
            const { all_stocks, selected_stocks } = await response.json();
            
            const selectionForm = this.dom.selectionForm;
            selectionForm.innerHTML = '';
            all_stocks.forEach(stock => {
                const isChecked = selected_stocks.includes(stock.nemo);
                selectionForm.innerHTML += `
                    <div class="col-md-4 col-sm-6">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" value="${stock.nemo}" id="kpi-stock-${stock.nemo}" ${isChecked ? 'checked' : ''}>
                            <label class="form-check-label" for="kpi-stock-${stock.nemo}">${stock.nemo}</label>
                        </div>
                    </div>`;
            });
        } catch (error) {
            console.error(error);
        }
    },

    filterStockSelection() {
        const filter = this.dom.stockSearchInput.value.toUpperCase();
        const labels = this.dom.selectionForm.querySelectorAll('.form-check');
        labels.forEach(label => {
            const text = label.textContent || label.innerText;
            label.parentNode.style.display = text.toUpperCase().includes(filter) ? '' : 'none';
        });
    },

    async handleSaveSelection() {
        const selectedNemos = Array.from(this.dom.selectionForm.querySelectorAll('input:checked')).map(input => input.value);
        try {
            await fetch('/api/kpi/selection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nemos: selectedNemos })
            });
            if (this.dom.selectionModal && typeof this.dom.selectionModal.hide === 'function') {
                this.dom.selectionModal.hide();
            }
            this.loadKpis();
        } catch (error) {
            console.error('Error al guardar la selección:', error);
        }
    },

    async handleUpdateClick() {
        const btn = this.dom.updateBtn;
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Actualizando...`;
        this.showAlert('Actualización de KPIs iniciada. Esto puede tardar varios minutos.', 'info', false);
        
        try {
            const response = await fetch('/api/kpis/update', { method: 'POST' });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error desconocido durante la actualización.');
            }
        } catch (error) {
            this.showAlert(error.message, 'danger');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Cargar/Actualizar KPIs';
        }
    },

    showAlert(message, type = 'info', autoHide = true) {
        const alertEl = this.dom.alert;
        if (!alertEl) return;
        alertEl.textContent = message;
        alertEl.className = `alert alert-${type}`;
        alertEl.classList.remove('d-none');
        
        if (autoHide) {
            setTimeout(() => alertEl.classList.add('d-none'), 5000);
        }
    },

    showRowDetails(data) {
        console.log('Detalles de la fila:', data);
    }
};

export default kpiManager;
