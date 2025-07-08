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
        this.socket = null;
    }

    initializeWidget(container) {
        if (!container) {
            console.warn('[KpiManager] Contenedor del widget no definido. Cancelando inicialización.');
            return;
        }
        this.kpiContent = container.querySelector('#kpi-content');
        this.kpiLoading = container.querySelector('#kpi-loading');

        if (!this.kpiContent || !this.kpiLoading) {
            console.error('[KPI Manager] No se encontró el contenedor de contenido o de carga para los KPIs. Abortando inicialización.');
            return;
        }

        this.dom = {
            table: this.kpiContent.querySelector('#kpiTable'),
            modal: this.kpiContent.querySelector('#kpiModal'),
            modalBody: this.kpiContent.querySelector('#kpiModalBody'),
            savePrefsBtn: this.kpiContent.querySelector('#saveKpiColumnPrefs'),
            configBtn: this.kpiContent.querySelector('#kpiConfigBtn'),
            refreshBtn: this.kpiContent.querySelector('#refreshKpisBtn'),
            // Nuevos elementos del formulario de configuración de prompt
            configModal: this.kpiContent.querySelector('#kpi-config-modal'),
            configForm: this.kpiContent.querySelector('#kpi-config-form'),
            saveConfigBtn: this.kpiContent.querySelector('#kpi-save-config-btn'),
        };
        
        this.socket = this.app.socket;
        
        if (!this.dom.table) {
            console.error('[KPI Manager] No se encontró la tabla de KPIs. Abortando inicialización.');
            return;
        }

        this.attachEventListeners();
        this.loadKpis();
        console.log('[KPI Manager] Widget inicializado.');
    }

    attachEventListeners() {
        console.log('[KPI Manager] Adjuntando listeners de eventos.');
        try {
            if (!this.socket) {
                console.error("[KPI Manager] Socket no está disponible. No se pueden adjuntar listeners.");
                return;
            }
            this.socket.on('kpi_update_complete', (data) => {
                console.log('[KPI Manager] Evento "kpi_update_complete" recibido:', data);
                const { message, alert_type } = data;
                this.app.uiManager.showAlert(message, alert_type);
                this.loadKpis();
            });

            this.dom.refreshBtn.addEventListener('click', () => this.loadKpis(true));
            // Los botones para las preferencias de columnas y config de prompt serán manejados por sus respectivas funciones
            // this.dom.configBtn.addEventListener('click', () => this.openConfigModal());
            // this.dom.saveConfigBtn.addEventListener('click', () => this.saveConfig());

        } catch (error) {
            console.error('[KPI Manager] Error al adjuntar listeners de eventos:', error);
        }
    }

    async loadKpis(forceUpdate = false) {
        console.log(`[KPI Manager] Iniciando carga de KPIs. Forzar actualización: ${forceUpdate}`);
        this.app.uiManager.toggleLoading(true, 'Cargando KPIs...');
        try {
            const data = await this.fetchData(forceUpdate);
            console.log('[KPI Manager] Datos de KPIs recibidos:', data);
            
            this.kpiData = data.kpis;
            this.columns = data.columns;
            this.columnPreferences = data.column_preferences;
            
            this.renderTable();
            console.log('[KPI Manager] Tabla de KPIs renderizada.');
            
        } catch (error) {
            console.error('[KPI Manager] Error al cargar los KPIs:', error);
            this.app.uiManager.showError('No se pudieron cargar los indicadores KPI.');
        } finally {
            console.log('[KPI Manager] Finalizó el proceso de carga de KPIs. Ocultando loader.');
            this.app.uiManager.toggleLoading(false);
        }
    }

    async fetchData(forceUpdate) {
        const url = `/api/kpis?force_update=${forceUpdate}`;
        console.log(`[KPI Manager] Realizando fetch a: ${url}`);
        const response = await fetch(url);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: 'Error desconocido del servidor' }));
            throw new Error(errorData.message || `Error del servidor: ${response.statusText}`);
        }
        return await response.json();
    }
    
    renderTable() {
        if (this.dataTable) {
            this.dataTable.destroy();
        }
        
        const visibleColumns = this.columnPreferences
            .filter(p => p.is_visible)
            .map(p => this.columns.find(c => c.key === p.column_key))
            .filter(Boolean);

        const tableHeaders = visibleColumns.map(c => `<th>${c.title}</th>`).join('');
        this.dom.table.querySelector('thead').innerHTML = `<tr>${tableHeaders}</tr>`;
        
        const dtColumns = visibleColumns.map(c => ({
            data: c.key,
            title: c.title,
            render: (data, type, row) => this.formatCell(c.key, data, row)
        }));

        this.dataTable = $(this.dom.table).DataTable({
            data: this.kpiData,
            columns: dtColumns,
            responsive: true,
            autoWidth: false,
            language: this.app.uiManager.getDataTablesLang(),
            dom: 'Bfrtip',
            buttons: ['copy', 'csv', 'excel', 'pdf', 'print']
        });
    }

    formatCell(key, data, row) {
        if (key.endsWith('_gtrend') && data) {
            return `<a href="${data}" target="_blank">Ver Tendencia</a>`;
        }
        if (typeof data === 'number') {
            return data.toLocaleString('es-CL');
        }
        if (typeof data === 'boolean') {
            return data ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-times text-danger"></i>';
        }
        return data || 'N/A';
    }

    // Funciones de configuración (a revisar/implementar según el nuevo enfoque)
    async openConfigModal() {
      // Lógica para abrir modal de configuración de prompt
    }
    
    async saveConfig() {
      // Lógica para guardar configuración de prompt
    }
}