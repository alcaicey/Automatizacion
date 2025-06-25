// src/static/js/kpiManager.js

window.kpiManager = {
    dataTable: null,
    dom: {},
    socket: null,
    updateTimeout: null, // Para manejar timeouts del lado del cliente
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
            const response = await fetch('/api/kpis'); 
            if (!response.ok) throw new Error('No se pudieron cargar los datos de KPIs.');
            const data = await response.json();
            this.renderTable(data);
        } catch (error) {
            console.error(error);
            this.showAlert(error.message, 'danger');
        }
    },
    
    async loadPreferences() { /* ... (sin cambios) ... */ },
    renderColumnModal() { /* ... (sin cambios) ... */ },
    async handleSavePrefs() { /* ... (sin cambios) ... */ },
    renderTable(data) { /* ... (sin cambios) ... */ },
    async openSelectionModal() { /* ... (sin cambios) ... */ },
    filterStockSelection() { /* ... (sin cambios) ... */ },
    async handleSaveSelection() { /* ... (sin cambios) ... */ },
    
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
            }, 300000); // 5 minutos

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
                alertEl.classList.add('d-none');
            }, 5000);
        }
    }
};