// src/static/js/managers/kpiManager.js

export default class KpiManager {
    constructor(app) {
        console.log('[KPI Manager] Constructor llamado.');
        this.app = app;
        this.dataTable = null;
        this.kpiData = [];
        this.columns = [];
        this.columnPreferences = [];
        this.dom = {};
        this.socket = null; // Se asignará en initializeWidget si es necesario
    }

    initializeWidget(container) {
        if (!container) {
            console.warn('[KPI Manager] Contenedor del widget no definido. Cancelando inicialización.');
            return;
        }

        // --- INICIO DE LA CORRECCIÓN ---
        // Buscamos los elementos directamente dentro del contenedor que nos pasan.
        this.dom = {
            table: container.querySelector('#kpiTable'),
            updateBtn: container.querySelector('#updateKPIsBtn'),
            alert: container.querySelector('#kpiUpdateAlert'),
            // ... (puedes añadir otros elementos que necesites controlar aquí)
        };
        // --- FIN DE LA CORRECCIÓN ---

        if (!this.dom.table || !this.dom.updateBtn) {
            console.error('[KPI Manager] Elementos esenciales como la tabla o el botón de actualizar no se encontraron. Abortando inicialización.');
            return;
        }
        
        this.socket = this.app.socket;

        this.attachEventListeners();
        this.loadKpis(); // Cargar los datos al inicializar
        console.log('[KPI Manager] Widget inicializado correctamente.');
    }

    attachEventListeners() {
        console.log('[KPI Manager] Adjuntando listeners de eventos.');
        
        this.dom.updateBtn.addEventListener('click', () => this.handleUpdateClick());

        if (this.socket) {
            this.socket.on('kpi_update_progress', (data) => {
                this.showFeedback(data.message, data.status || 'info');
            });

            this.socket.on('kpi_update_complete', (data) => {
                const message = data.error ? `Error: ${data.error}` : data.message;
                const type = data.error ? 'danger' : 'success';
                this.showFeedback(message, type);
                
                this.dom.updateBtn.disabled = false;
                this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Cargar/Actualizar KPIs';
                
                if (!data.error) {
                    this.loadKpis(); // Recargar la tabla si la actualización fue exitosa
                }
            });
        }
    }

    async handleUpdateClick() {
        this.dom.updateBtn.disabled = true;
        this.dom.updateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Actualizando...';
        this.showFeedback('Iniciando proceso de actualización de KPIs...', 'info');

        try {
            // Llama al endpoint de la API para iniciar la actualización de KPIs
            const response = await this.app.fetchData('/api/kpis/update', { method: 'POST' });
            // El servidor responderá inmediatamente, y el progreso se recibirá por Socket.IO
        } catch (error) {
            this.showFeedback(`Error al iniciar la actualización: ${error.message}`, 'danger');
            this.dom.updateBtn.disabled = false;
            this.dom.updateBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Cargar/Actualizar KPIs';
        }
    }

    async loadKpis() {
        console.log('[KPI Manager] Iniciando carga de KPIs.');
        this.showFeedback('Cargando indicadores...', 'info', true); // `true` para mostrar spinner

        try {
            const kpiDataFromApi = await this.app.fetchData('/api/kpis');
            this.kpiData = Array.isArray(kpiDataFromApi) ? kpiDataFromApi : [];
            this.renderTable();
            
            const message = this.kpiData.length > 0 
                ? `Se cargaron ${this.kpiData.length} indicadores.` 
                : 'No hay datos de KPIs para mostrar.';
            this.showFeedback(message, 'success');

        } catch (error) {
            console.error('[KPI Manager] Fallo al cargar KPIs:', error);
            
            // Estado de recuperación: asegurar que la tabla quede vacía
            this.kpiData = [];
            this.renderTable();
            
            // Informar al usuario
            this.showFeedback(`Error al cargar KPIs: ${error.message}`, 'danger');
        }
    }
    
    renderTable() {
        if (this.dataTable) {
            this.dataTable.destroy();
            this.dataTable = null; // Buena práctica para asegurar limpieza completa
        }

        // --- INICIO DE LA CORRECCIÓN ---

        // 1. Definir las columnas que ESPERAMOS, independientemente de los datos.
        const defaultColumns = [
            { data: 'nemo', title: 'Símbolo' },
            { data: 'precio_cierre_ant', title: 'Precio Cierre Ant.' },
            { data: 'razon_pre_uti', title: 'Razón P/U' },
            { data: 'roe', title: 'ROE' },
            { data: 'dividend_yield', title: 'Div. Yield' },
            { data: 'riesgo', title: 'Riesgo' },
            { data: 'kpi_last_updated', title: 'Últ. Act. KPI' },
            { data: 'kpi_source', title: 'Fuente KPI' }
        ];

        let dtColumns = [];

        // 2. Si tenemos datos, usamos sus claves para asegurar que las columnas coincidan.
        //    Si no, usamos las columnas por defecto.
        if (this.kpiData && this.kpiData.length > 0 && Object.keys(this.kpiData[0]).length > 0) {
            dtColumns = Object.keys(this.kpiData[0]).map(key => {
                const defaultColumn = defaultColumns.find(c => c.data === key);
                return {
                    data: key,
                    title: defaultColumn ? defaultColumn.title : key.replace(/_/g, ' ').toUpperCase()
                };
            });
        } else {
            // Si no hay datos, usamos las cabeceras por defecto para que DataTables no falle.
            dtColumns = defaultColumns;
        }
        // --- FIN DE LA CORRECCIÓN ---

        this.dataTable = $(this.dom.table).DataTable({
            data: this.kpiData, // Esto puede ser un array vacío, está bien.
            columns: dtColumns, // Esto AHORA NUNCA será un array vacío.
            responsive: true,
            autoWidth: false,
            dom: 'Bfrtip',
            buttons: ['excel', 'csv'],
            // Añadimos esto para que muestre el mensaje correcto cuando no hay datos
            language: {
                ...this.app.uiManager.getDataTablesLang(),
                emptyTable: "No hay datos de KPIs para mostrar. Seleccione acciones en la configuración."
            }
        });
    }

    showFeedback(message, type = 'info', isLoading = false) {
        if (!this.dom.alert) return;
        
        // Limpiar clases anteriores y añadir la nueva
        this.dom.alert.className = `alert alert-${type} d-flex align-items-center`;
        
        let content = '';
        if (isLoading) {
            content += '<div class="spinner-border spinner-border-sm me-2" role="status"></div>';
        }
        content += `<span>${message}</span>`;
        
        this.dom.alert.innerHTML = content;
        this.dom.alert.classList.remove('d-none');
    }

    // ... (resto de métodos como formatCell, etc. pueden ser añadidos después)
}