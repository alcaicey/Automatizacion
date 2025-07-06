// src/static/js/closingManager.js

const closingManager = {
    app: null, // Referencia a la instancia de la App
    dataTable: null,
    dom: {},
    socket: null,
    isInitialized: false,
    columnPrefs: {
        all: [],
        visible: [],
    },
    columnConfig: {
        'nemo': { title: 'Símbolo' },
        'fec_fij_cie': { title: 'Fecha Cierre', render: (d) => d ? new Date(d + 'T00:00:00Z').toLocaleDateString('es-CL', { timeZone: 'UTC' }) : '' },
        'precio_cierre_ant': { title: 'Precio Cierre', render: (d) => d != null ? d.toLocaleString('es-CL', { style: 'currency', currency: 'CLP' }) : 'N/A' },
        'monto_ant': { title: 'Monto Transado', render: (d) => d != null ? d.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }) : 'N/A' },
        'un_transadas_ant': { title: 'Unidades', render: (d) => d != null ? d.toLocaleString('es-CL') : 'N/A' },
        'neg_ant': { title: 'N° Negocios' },
        'ren_actual': { title: 'Rend. Actual (%)' },
        'razon_pre_uti': { title: 'Razón P/U' },
        'PERTENECE_IPSA': { title: 'IPSA', render: (d) => d ? '<i class="fas fa-check text-success"></i>' : '' },
        'PERTENECE_IGPA': { title: 'IGPA', render: (d) => d ? '<i class="fas fa-check text-success"></i>' : '' },
        'PESO_IPSA': { title: 'Peso IPSA (%)' },
        'PESO_IGPA': { title: 'Peso IGPA (%)' },
    },

    init(appInstance) {
        this.app = appInstance;
        console.log('[ClosingManager] Módulo inicializado y en espera de su widget.');
        
        // La función de flecha asegura que 'this' dentro del callback
        // es el objeto 'closingManager'.
        document.addEventListener('widgetAdded', (event) => {
            const widgetElement = event.detail.element;
            if (widgetElement.querySelector('#closingTable')) {
                this.setupWidget(widgetElement);
            }
        });

        this.attachSocketListeners();
    },

    setupWidget(widgetElement) {
        if (this.isInitialized) return;
        console.log('[ClosingManager] Widget de Cierre Bursátil detectado. Configurando...');

        this.dom = {
            updateBtn: widgetElement.querySelector('#updateClosingBtn'),
            table: widgetElement.querySelector('#closingTable'),
            alert: widgetElement.querySelector('#closingUpdateAlert'),
            filterSwitch: widgetElement.querySelector('#filterClosingByPortfolio'),
            columnBtn: widgetElement.querySelector('#closingColumnBtn'),
            columnModal: document.getElementById('closingColumnConfigModal'),
            columnForm: document.getElementById('closingColumnConfigForm'),
            saveColumnPrefsBtn: document.getElementById('saveClosingColumnPrefs'),
        };

        this.attachWidgetEventListeners();
        this.loadPreferences().then(() => {
            this.loadClosings();
        });
        
        this.isInitialized = true;
    },

    attachSocketListeners() {
        if (!this.app || !this.app.socket) return;
        this.app.socket.on('closing_update_complete', (result) => {
            if (!this.isInitialized) return;
            
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Actualizar';
            this.dom.updateBtn.disabled = false;
            
            this.displayUpdateResult(result);

            if (!result.error) {
                console.log('[ClosingManager] Actualización de cierre completa, recargando datos de la tabla...');
                this.loadClosings();
            }
        });
    },

    attachWidgetEventListeners() {
        this.dom.updateBtn.addEventListener('click', () => this.handleUpdateClick());
        this.dom.saveColumnPrefsBtn.addEventListener('click', () => this.handleSavePrefs());
        this.dom.filterSwitch.addEventListener('change', () => this.loadClosings());
    },

    async loadClosings() {
        if (!this.isInitialized) return;
        this.app.uiManager.toggleLoading(true, 'Cargando datos de cierre...');
        try {
            const url = new URL(window.location.origin + '/api/closing');
            
            if (this.dom.filterSwitch && this.dom.filterSwitch.checked) {
                const holdings = this.app.portfolioManager ? this.app.portfolioManager.state.holdings : [];
                if (holdings.length > 0) {
                    const portfolioSymbols = holdings.map(h => h.symbol);
                    portfolioSymbols.forEach(nemo => url.searchParams.append('nemo', nemo));
                } else {
                    console.log('[ClosingManager] Filtro de portafolio activo, pero no hay holdings. Mostrando tabla vacía.');
                    this.renderTable([]);
                    this.app.uiManager.toggleLoading(false);
                    return;
                }
            }

            const response = await fetch(url);
            if (!response.ok) throw new Error('No se pudieron cargar los datos de cierre.');
            const data = await response.json();
            this.renderTable(data);
        } catch (error) {
            console.error('Error al cargar datos de cierre:', error);
            this.renderTable([]);
        } finally {
            this.app.uiManager.toggleLoading(false);
        }
    },
    
    async loadPreferences() {
        try {
            const res = await fetch('/api/closing/columns');
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
        if (!this.dom.columnForm) return;
        this.dom.columnForm.innerHTML = '';
        this.columnPrefs.all.forEach(colKey => {
            const isChecked = this.columnPrefs.visible.includes(colKey);
            const label = this.columnConfig[colKey]?.title || colKey.replace(/_/g, ' ');
            this.dom.columnForm.innerHTML += `
                <div class="col-6"><div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${colKey}" id="close-col-${colKey}" ${isChecked ? 'checked' : ''}>
                    <label class="form-check-label" for="close-col-${colKey}">${label}</label>
                </div></div>`;
        });
    },

    renderTable(data) {
        if (!this.isInitialized || !this.dom.table) return;

        if ($.fn.DataTable.isDataTable(this.dom.table)) {
            this.dataTable.clear().rows.add(data).draw();
        } else {
            const columns = this.columnPrefs.visible.map(key => ({
                data: key,
                title: this.columnConfig[key]?.title || key.replace(/_/g, ' '),
                render: this.columnConfig[key]?.render || null,
            }));

            this.dataTable = $(this.dom.table).DataTable({
                data,
                columns,
                order: [[0, 'asc']],
                responsive: true,
                language: this.app.uiManager.getDataTablesLang(),
                dom: 'Bfrtip',
                buttons: ['excelHtml5', 'csvHtml5'],
            });
        }
    },
    
    async handleSavePrefs() {
        const selected = Array.from(this.dom.columnForm.querySelectorAll('input:checked')).map(i => i.value);
        this.columnPrefs.visible = selected;
        
        await fetch('/api/closing/columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: selected })
        });

        bootstrap.Modal.getInstance(this.dom.columnModal).hide();
        this.dataTable.destroy();
        $(this.dom.table).empty();
        this.renderTable(this.dataTable.rows().data().toArray());
    },

    async handleUpdateClick() {
        this.dom.updateBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Actualizando...`;
        this.dom.updateBtn.disabled = true;
        this.dom.alert.classList.add('d-none');

        try {
            const response = await fetch('/api/closing/update', { method: 'POST' });
            if (response.status !== 202) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'El servidor no pudo iniciar el proceso.');
            }
        } catch (error) {
            this.displayUpdateResult({ error: error.message });
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Actualizar';
            this.dom.updateBtn.disabled = false;
        }
    },
    
    displayUpdateResult(result) {
        const alertEl = this.dom.alert;
        if (result.error) {
            alertEl.className = 'alert alert-danger';
            alertEl.innerHTML = `<strong>Error:</strong> ${result.error}`;
        } else {
            alertEl.className = 'alert alert-success';
            alertEl.textContent = `¡Actualización completada! Se procesaron ${result.processed_count} registros de cierre.`;
        }
        alertEl.classList.remove('d-none');
    }
};

// La inicialización se maneja centralmente desde app.js, por lo que este listener global ya no es necesario aquí.
// document.addEventListener('DOMContentLoaded', () => {
//     closingManager.init();
// });