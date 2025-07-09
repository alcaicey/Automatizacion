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
        this.showFeedback('Iniciando análisis en el servidor...', 'info', true);

        try {
            const response = await this.app.fetchData('/api/drainers/analyze', { method: 'POST' });
            // El servidor responderá, pero el progreso y resultado final vendrán por socket.
            // La respuesta inicial podría ser simplemente un ack.
            this.showFeedback(response.message || 'Análisis iniciado. Esperando progreso...', 'info', true);
        } catch (error) {
            this.showFeedback(`Error al iniciar análisis: ${error.message}`, 'danger');
            this.isAnalyzing = false;
            this.dom.runBtn.disabled = false;
            this.dom.runBtn.innerHTML = '<i class="fas fa-play-circle me-2"></i>Ejecutar Análisis';
        }
    }

    async fetchEvents() {
        if(!this.isInitialized) return;
        this.showFeedback('Cargando eventos...', 'info', true);
        try {
            const events = await this.app.fetchData('/api/drainers/events');
            this.dataTable.clear().rows.add(events || []).draw();
            this.showFeedback(`Se cargaron ${events.length} eventos.`, 'success');
        } catch (error) {
            this.showFeedback(`Error al cargar eventos: ${error.message}`, 'danger');
            this.dataTable.clear().draw(); // Limpiar tabla en caso de error
        }
    }

    showFeedback(message, type = 'info', isLoading = false) {
        if (!this.dom.alert) return;

        const alert = this.dom.alert;
        alert.className = `alert alert-${type} d-flex align-items-center`;
        
        let content = '';
        if (isLoading) {
            content += '<div class="spinner-border spinner-border-sm me-2" role="status"></div>';
        }
        content += `<span>${message}</span>`;
        
        alert.innerHTML = content;
        alert.classList.remove('d-none');

        // Ocultar automáticamente si no es un estado de carga o de información persistente
        if (!isLoading && type !== 'info') {
            setTimeout(() => alert.classList.add('d-none'), 5000);
        }
    }
}