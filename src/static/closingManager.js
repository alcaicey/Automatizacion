// src/static/js/closingManager.js

window.closingManager = {
    dataTable: null,
    dom: {},
    socket: null,
    // --- NUEVO: Objeto para preferencias de columnas ---
    columnPrefs: {
        all: [],
        visible: [],
        config: {
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
        }
    },

    init() {
        this.dom = {
            updateBtn: document.getElementById('updateClosingBtn'),
            table: document.getElementById('closingTable'),
            alert: document.getElementById('closingUpdateAlert'),
            // --- NUEVO: DOM para el modal de columnas ---
            columnBtn: document.getElementById('closingColumnBtn'),
            columnModal: document.getElementById('closingColumnConfigModal'),
            columnForm: document.getElementById('closingColumnConfigForm'),
            saveColumnPrefsBtn: document.getElementById('saveClosingColumnPrefs'),
        };

        if (!this.dom.table) return;

        this.socket = io();
        this.attachEventListeners();
        this.loadInitialData(); // <-- NUEVA FUNCIÓN
        console.log('[ClosingManager] Módulo inicializado.');
    },

    async loadInitialData() {
        await this.loadPreferences();
        await this.loadClosings();
    },
    
    // --- NUEVA FUNCIÓN ---
    async loadPreferences() {
        try {
            const res = await fetch('/api/closing/columns');
            if (!res.ok) throw new Error('No se pudieron cargar las preferencias de columnas de cierre.');
            const data = await res.json();
            this.columnPrefs.all = data.all_columns;
            this.columnPrefs.visible = data.visible_columns;
            this.renderColumnModal();
        } catch (error) {
            console.error(error);
        }
    },
    
    // --- NUEVA FUNCIÓN ---
    renderColumnModal() {
        this.dom.columnForm.innerHTML = '';
        this.columnPrefs.all.forEach(colKey => {
            const isChecked = this.columnPrefs.visible.includes(colKey);
            const label = this.columnPrefs.config[colKey]?.title || colKey.replace(/_/g, ' ');
            this.dom.columnForm.innerHTML += `
                <div class="col-6"><div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${colKey}" id="close-col-${colKey}" ${isChecked ? 'checked' : ''}>
                    <label class="form-check-label" for="close-col-${colKey}">${label}</label>
                </div></div>`;
        });
    },

    attachEventListeners() {
        this.dom.updateBtn.addEventListener('click', () => this.handleUpdateClick());
        this.dom.saveColumnPrefsBtn.addEventListener('click', () => this.handleSavePrefs()); // <-- NUEVO

        this.socket.on('closing_update_complete', (result) => {
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Actualizar Datos de Cierre';
            this.dom.updateBtn.disabled = false;
            this.displayUpdateResult(result);
            if (!result.error) {
                this.loadClosings();
            }
        });
    },

    async loadClosings() {
        try {
            const response = await fetch('/api/closing');
            if (!response.ok) throw new Error('No se pudieron cargar los datos de cierre.');
            const data = await response.json();
            this.renderTable(data);
        } catch (error) {
            console.error('Error al cargar datos de cierre:', error);
        }
    },
    
    // --- MODIFICADO ---
    renderTable(data) {
        if (this.dataTable) {
            this.dataTable.destroy();
        }
        $(this.dom.table).empty();

        const columns = this.columnPrefs.visible.map(key => ({
            data: key,
            title: this.columnPrefs.config[key]?.title || key.replace(/_/g, ' '),
            render: this.columnPrefs.config[key]?.render || null,
        }));

        this.dataTable = $(this.dom.table).DataTable({
            data,
            columns,
            order: [[0, 'asc']],
            responsive: true,
            language: { url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
            dom: 'Bfrtip',
            buttons: ['excelHtml5', 'csvHtml5'],
        });
    },
    
    // --- NUEVA FUNCIÓN ---
    async handleSavePrefs() {
        const selected = Array.from(this.dom.columnForm.querySelectorAll('input:checked')).map(i => i.value);
        this.columnPrefs.visible = selected;
        
        await fetch('/api/closing/columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: selected })
        });

        bootstrap.Modal.getInstance(this.dom.columnModal).hide();
        // Re-renderizar la tabla con las nuevas columnas visibles
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
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Actualizar Datos de Cierre';
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