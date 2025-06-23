// src/static/js/kpiManager.js

window.kpiManager = {
    dataTable: null,
    dom: {},
    socket: null,

    columnConfig: {
        'nemo': { title: 'Empresa' },
        'precio_cierre_ant': { title: 'Precio', render: (d) => d ? d.toLocaleString('es-CL', { style: 'currency', currency: 'CLP' }) : 'N/A' },
        'razon_pre_uti': { title: 'P/E' },
        'roe': { title: 'ROE (%)', defaultContent: '<i>N/A</i>' },
        'dividend_yield': { title: 'Yield (%)' },
        'riesgo': { 
            title: 'Riesgo/Consenso', 
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
        'beta': { title: 'Beta', defaultContent: '<i>N/A</i>' },
        'debt_to_equity': { title: 'Deuda/Patr.', defaultContent: '<i>N/A</i>' },
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

        this.socket.on('kpi_update_progress', (data) => {
            const message = `[${data.progress}] Procesando ${data.nemo}... (${data.status})`;
            this.showAlert(message, 'info', false);
        });
        this.socket.on('kpi_update_complete', (data) => {
            this.dom.updateBtn.disabled = false;
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Cargar/Actualizar KPIs con IA';
            this.showAlert(data.message, 'success');
            this.loadInitialData();
        });
    },

    async loadInitialData() {
        this.renderTable([]);
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

    renderTable(data) {
        if (this.dataTable) this.dataTable.destroy();
        $(this.dom.table).empty();

        const columns = Object.keys(this.columnConfig).map(key => ({
            data: key,
            title: this.columnConfig[key].title,
            render: this.columnConfig[key].render,
            defaultContent: this.columnConfig[key].defaultContent || ''
        }));

        this.dataTable = $(this.dom.table).DataTable({
            data,
            columns,
            order: [[0, 'asc']],
            responsive: true,
            language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
            dom: 'Bfrtip',
            buttons: ['excelHtml5', 'csvHtml5'],
        });
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
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Cargar/Actualizar KPIs con IA';
        }
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
            this.loadInitialData();
        } catch (error) {
            this.showAlert(error.message, 'danger');
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