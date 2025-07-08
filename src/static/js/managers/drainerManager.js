// src/static/js/managers/drainerManager.js

export default class DrainerManager {
    constructor(app) {
        this.app = app;
        this.uiManager = app.uiManager;
        this.dataTable = null;
        this.dom = {};
        this.isInitialized = false;
        this.isAnalyzing = false;
    }

    initializeWidget(container) {
        if (!container) {
            console.warn('[DrainerManager] Contenedor del widget no definido. Cancelando inicialización.');
            return;
        }
        this.clearHistoryBtn = container.querySelector('#clear-history-btn');
        this.clearPricesBtn = container.querySelector('#clear-prices-btn');

        if (this.isInitialized) return;
        console.log("[DrainerManager] Widget de Drainers detectado. Configurando...");

        this.dom = {
            runBtn: container.querySelector('#runAnalysisBtn'),
            table: container.querySelector('#drainersTable'),
            alert: container.querySelector('#drainerAlert')
        };
        
        this.socket = this.app.socket; // Asumiendo que app tiene la instancia de socket
        
        this.setupDataTable();
        this.attachWidgetEventListeners();
        this.attachSocketListeners();
        this.fetchEvents();
        this.isInitialized = true;
    }
    
    attachSocketListeners() {
        if (!this.socket) return;
        this.socket.on('drainer_progress', (data) => {
            if (this.isInitialized) this.showFeedback(data.message, data.status);
        });
        this.socket.on('drainer_complete', (data) => {
            if (this.isInitialized) {
                this.isAnalyzing = false;
                this.dom.runBtn.disabled = false;
                this.dom.runBtn.innerHTML = '<i class="fas fa-play-circle me-2"></i>Ejecutar Análisis';
                this.showFeedback(data.message, data.status);
                this.fetchEvents();
            }
        });
    }

    setupDataTable() {
        if ($.fn.DataTable.isDataTable(this.dom.table)) {
            $(this.dom.table).DataTable().destroy();
        }

        this.dataTable = $(this.dom.table).DataTable({
            data: [],
            columns: [
                { data: 'event_date', title: 'Fecha', render: data => data ? new Date(data).toLocaleDateString() : 'N/A' },
                { data: 'nemo', title: 'Símbolo' },
                { data: 'event_type', title: 'Tipo' },
                { data: 'description', title: 'Descripción', className: 'text-wrap' },
                { data: 'source', title: 'Fuente' },
                { 
                    data: 'price_change_pct', 
                    title: 'Cambio Precio (5d)',
                    render: (data) => {
                        if (data === null || data === undefined) return 'N/A';
                        const value = parseFloat(data);
                        const color = value > 0 ? 'text-success' : value < 0 ? 'text-danger' : 'text-muted';
                        return `<span class="fw-bold ${color}">${value.toFixed(2)}%</span>`;
                    }
                }
            ],
            responsive: true, autoWidth: false,
            language: this.app.uiManager.getDataTablesLang(),
            order: [[0, 'desc']]
        });
    }

    attachWidgetEventListeners() {
        this.dom.runBtn.addEventListener('click', () => this.runAnalysis());
    }

    async runAnalysis() {
        if (this.isAnalyzing) return;
        this.isAnalyzing = true;
        this.dom.runBtn.disabled = true;
        this.dom.runBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analizando...';
        this.showFeedback('Iniciando análisis en el servidor...', 'info');

        try {
            const response = await fetch('/api/drainers/analyze', { method: 'POST' });
            if (!response.ok) throw new Error((await response.json()).message);
            this.showFeedback((await response.json()).message, 'info');
        } catch (error) {
            this.showFeedback(`Error: ${error.message}`, 'danger');
            this.isAnalyzing = false;
            this.dom.runBtn.disabled = false;
        }
    }

    async fetchEvents() {
        if(!this.isInitialized) return;
        try {
            const response = await fetch('/api/drainers/events');
            if (!response.ok) throw new Error('No se pudieron cargar los eventos.');
            const events = await response.json();
            this.dataTable.clear().rows.add(events).draw();
        } catch (error) {
            this.showFeedback(`Error al cargar eventos: ${error.message}`, 'danger');
        }
    }

    showFeedback(message, type = 'info') {
        if (!this.dom.alert) return;
        this.dom.alert.className = `alert alert-${type} alert-dismissible fade show`;
        this.dom.alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
    }
}