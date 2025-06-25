// src/static/js/closingManager.js

window.closingManager = {
    dataTable: null,
    dom: {},
    socket: null,
    columnPrefs: {
        all: [],
        visible: [],
    },
    columnConfig: {
        'nemo': { title: 'Símbolo' },
        'fec_fij_cie': { title: 'Fecha Cierre', render: (d) => new Date(d + 'T00:00:00Z').toLocaleDateString('es-CL', { timeZone: 'UTC' }) },
        'precio_cierre_ant': { title: 'Precio Cierre', render: (d) => d ? d.toLocaleString('es-CL', { style: 'currency', currency: 'CLP' }) : 'N/A' },
        'monto_ant': { title: 'Monto Transado', render: (d) => d ? d.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', minimumFractionDigits: 0 }) : 'N/A' },
        'un_transadas_ant': { title: 'Unidades', render: (d) => d ? d.toLocaleString('es-CL') : 'N/A' },
        'neg_ant': { title: 'N° Negocios' },
        'ren_actual': { title: 'Rend. Actual (%)' },
        'razon_pre_uti': { title: 'Razón P/U' },
        'PERTENECE_IPSA': { title: 'IPSA', render: (d) => d ? '<i class="fas fa-check text-success"></i>' : '' },
        'PERTENECE_IGPA': { title: 'IGPA', render: (d) => d ? '<i class="fas fa-check text-success"></i>' : '' },
        'PESO_IPSA': { title: 'Peso IPSA (%)' },
        'PESO_IGPA': { title: 'Peso IGPA (%)' },
    },

    init() {
        // --- INICIO DE LA CORRECCIÓN: Guardar el contexto ---
        const self = this; 
        // --- FIN DE LA CORRECCIÓN ---

        self.dom = {
            updateBtn: document.getElementById('updateClosingBtn'),
            table: document.getElementById('closingTable'),
            alert: document.getElementById('closingUpdateAlert'),
            filterSwitch: document.getElementById('filterClosingByPortfolio'),
            columnBtn: document.getElementById('closingColumnBtn'),
            columnModal: document.getElementById('closingColumnConfigModal'),
            columnForm: document.getElementById('closingColumnConfigForm'),
            saveColumnPrefsBtn: document.getElementById('saveClosingColumnPrefs'),
        };

        if (!self.dom.table) return;

        self.socket = io();
        self.attachEventListeners();
        self.loadPreferences(); 
        
        console.log('[ClosingManager] Módulo inicializado.');
    },

    attachEventListeners() {
        const self = this;
        self.dom.updateBtn.addEventListener('click', () => self.handleUpdateClick());
        self.dom.saveColumnPrefsBtn.addEventListener('click', () => self.handleSavePrefs());
        self.dom.filterSwitch.addEventListener('change', () => self.loadClosings());

        self.socket.on('closing_update_complete', (result) => {
            self.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Actualizar';
            self.dom.updateBtn.disabled = false;
            self.displayUpdateResult(result);
            if (!result.error) {
                self.loadClosings();
            }
        });
    },

    async loadClosings() {
        const self = this;
        try {
            let nemos_to_filter = [];
            if (self.dom.filterSwitch && self.dom.filterSwitch.checked) {
                if (window.portfolioManager && window.portfolioManager.holdings.length > 0) {
                    nemos_to_filter = window.portfolioManager.holdings.map(h => h.symbol);
                } else if (window.portfolioManager && window.portfolioManager.holdings.length === 0) {
                    self.renderTable([]);
                    return;
                }
            }

            const url = new URL(window.location.origin + '/api/closing');
            if (nemos_to_filter.length > 0) {
                nemos_to_filter.forEach(nemo => url.searchParams.append('nemo', nemo));
            }

            const response = await fetch(url);
            if (!response.ok) throw new Error('No se pudieron cargar los datos de cierre.');
            const data = await response.json();
            self.renderTable(data);
        } catch (error) {
            console.error('Error al cargar datos de cierre:', error);
            if (self.dataTable) {
                self.dataTable.clear().draw();
            }
        }
    },
    
    async loadPreferences() {
        const self = this;
        try {
            const res = await fetch('/api/closing/columns');
            if (!res.ok) throw new Error('No se pudieron cargar las preferencias de columnas.');
            const data = await res.json();
            self.columnPrefs.all = data.all_columns;
            self.columnPrefs.visible = data.visible_columns;
            self.renderColumnModal();
        } catch (error) {
            console.error(error);
        }
    },
    
    renderColumnModal() {
        const self = this;
        self.dom.columnForm.innerHTML = '';
        self.columnPrefs.all.forEach(colKey => {
            const isChecked = self.columnPrefs.visible.includes(colKey);
            const label = self.columnConfig[colKey]?.title || colKey.replace(/_/g, ' ');
            self.dom.columnForm.innerHTML += `
                <div class="col-6"><div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${colKey}" id="close-col-${colKey}" ${isChecked ? 'checked' : ''}>
                    <label class="form-check-label" for="close-col-${colKey}">${label}</label>
                </div></div>`;
        });
    },

    renderTable(data) {
        const self = this;
        if (self.dataTable) {
            self.dataTable.destroy();
        }
        $(self.dom.table).empty();

        const columns = self.columnPrefs.visible.map(key => ({
            data: key,
            title: self.columnConfig[key]?.title || key.replace(/_/g, ' '),
            render: self.columnConfig[key]?.render || null,
        }));

        self.dataTable = $(self.dom.table).DataTable({
            data,
            columns,
            order: [[0, 'asc']],
            responsive: true,
            language: { url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
            dom: 'Bfrtip',
            buttons: ['excelHtml5', 'csvHtml5'],
        });
    },
    
    async handleSavePrefs() {
        const self = this;
        const selected = Array.from(self.dom.columnForm.querySelectorAll('input:checked')).map(i => i.value);
        self.columnPrefs.visible = selected;
        
        await fetch('/api/closing/columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: selected })
        });

        bootstrap.Modal.getInstance(self.dom.columnModal).hide();
        self.renderTable(self.dataTable.rows().data().toArray());
    },

    async handleUpdateClick() {
        const self = this;
        self.dom.updateBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Actualizando...`;
        self.dom.updateBtn.disabled = true;
        self.dom.alert.classList.add('d-none');

        try {
            const response = await fetch('/api/closing/update', { method: 'POST' });
            if (response.status !== 202) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'El servidor no pudo iniciar el proceso.');
            }
        } catch (error) {
            self.displayUpdateResult({ error: error.message });
            self.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Actualizar';
            self.dom.updateBtn.disabled = false;
        }
    },
    
    displayUpdateResult(result) {
        const self = this;
        const alertEl = self.dom.alert;
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