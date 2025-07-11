// src/static/dashboardLayout.js

class DashboardLayout {
    constructor() {
        this.grid = null;
        this.WIDGET_DEFINITIONS = this.getWidgetDefinitions();
        this.init();
    }
    
    init() {
        this.grid = GridStack.init({ float: true, cellHeight: '70px', minRow: 1, handle: '.widget-header' });
        this.loadLayout();
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.grid.on('change', () => this.saveLayout());
        
        document.getElementById('widget-list').addEventListener('click', (e) => {
            e.preventDefault();
            if (e.target.tagName === 'A') this.addWidget(e.target.dataset.widgetId);
        });

        // Evento clave: cuando GridStack AÑADE un widget, lo notificamos
        this.grid.on('added', (event, items) => {
            items.forEach(item => {
                document.dispatchEvent(new CustomEvent('widgetAdded', { 
                    detail: { element: item.el, widgetId: item.id } 
                }));
            });
        });
    }

    getWidgetDefinitions() {
        return {
            'portfolio': { content: `<div class="widget-header"><h5><i class="fas fa-briefcase me-2"></i>Mi Portafolio</h5><div class="widget-controls"><button type="button" class="btn btn-sm btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#portfolioColumnConfigModal"><i class="fas fa-sliders-h"></i></button><button type="button" class="btn btn-sm btn-danger remove-widget-btn"><i class="fas fa-times"></i></button></div></div><div class="widget-body"><div class="table-responsive"><table id="portfolioTable" class="table table-bordered table-hover w-100"><thead class="table-dark"></thead><tbody id="portfolioTableBody"></tbody><tfoot><tr class="table-group-divider" style="font-size: 1.1rem;"><th colspan="3" class="text-end"><h5>Totales:</h5></th><th id="footerTotalPaid"></th><th colspan="2"></th><th id="footerTotalCurrentValue"></th><th id="footerTotalGainLoss"></th><th id="footerTotalGainLossPercent"></th><th></th></tr></tfoot></table></div></div>`, options: { w: 12, h: 6, minW: 6, minH: 4, id: 'portfolio' } },
            'market-data': { content: `<div class="widget-header"><h5><i class="fas fa-table me-2"></i>Datos del Mercado</h5><div class="widget-controls"><button type="button" class="btn btn-sm btn-outline-secondary" data-bs-toggle="modal" data-bs-target="#columnConfigModal"><i class="fas fa-sliders-h"></i></button><button type="button" class="btn btn-sm btn-danger remove-widget-btn"><i class="fas fa-times"></i></button></div></div><div class="widget-body"><div class="table-responsive"><table id="stocksTable" class="table table-striped table-hover w-100"></table></div></div>`, options: { w: 12, h: 7, minW: 6, minH: 4, id: 'market-data' } },
            'closing-data': { content: `<div class="widget-header"><h5><i class="fas fa-door-closed me-2"></i>Cierre Bursátil Anterior</h5><div class="widget-controls"><button type="button" class="btn btn-sm btn-danger remove-widget-btn"><i class="fas fa-times"></i></button></div></div><div class="widget-body"><div class="d-flex justify-content-between align-items-center mb-3 gap-2 flex-wrap"><div class="form-check form-switch"><input class="form-check-input" type="checkbox" role="switch" id="filterClosingByPortfolio" checked><label class="form-check-label" for="filterClosingByPortfolio">Solo mi portafolio</label></div><div class="d-flex gap-2"><button id="updateClosingBtn" class="btn btn-info btn-sm"><i class="fas fa-sync-alt"></i> Actualizar</button><button id="closingColumnBtn" class="btn btn-secondary btn-sm" data-bs-toggle="modal" data-bs-target="#closingColumnConfigModal"><i class="fas fa-sliders-h"></i> Columnas</button></div></div><div id="closingUpdateAlert" class="alert d-none" role="alert"></div><div class="table-responsive"><table id="closingTable" class="table table-striped table-hover w-100"></table></div></div>`, options: { w: 12, h: 7, minW: 6, minH: 4, id: 'closing-data' } },
            'controls': { content: `<div class="widget-header"><h5><i class="fas fa-cogs me-2"></i>Configuración y Acciones</h5><div class="widget-controls"><button type="button" class="btn btn-sm btn-danger remove-widget-btn"><i class="fas fa-times"></i></button></div></div><div class="widget-body"><form id="stockFilterForm" class="mb-3 p-2 border rounded bg-body-tertiary small"><label class="form-label fw-bold">Filtrar Datos del Mercado:</label><div class="row g-2"><div class="col-6"><input type="text" class="form-control form-control-sm stock-code" placeholder="COPEC"></div><div class="col-6"><input type="text" class="form-control form-control-sm stock-code" placeholder="SQM-B"></div><div class="col-6"><input type="text" class="form-control form-control-sm stock-code" placeholder="CMPC"></div><div class="col-6"><input type="text" class="form-control form-control-sm stock-code" placeholder="FALABELLA"></div></div><div class="form-check form-switch mt-2"><input class="form-check-input" type="checkbox" role="switch" id="allStocksCheck" checked><label class="form-check-label" for="allStocksCheck">Todas</label></div><div class="d-flex justify-content-end gap-2 mt-2"><button type="button" id="clearBtn" class="btn btn-sm btn-outline-secondary">Limpiar</button><button type="submit" class="btn btn-sm btn-primary">Aplicar</button></div></form><form id="portfolioForm" class="mb-3 p-2 border rounded bg-body-tertiary small"><label class="form-label fw-bold">Añadir Activo:</label><div class="row g-2 align-items-end"><div class="col-12"><input type="text" id="portfolioSymbol" class="form-control form-control-sm" placeholder="Símbolo" required></div><div class="col-6"><input type="number" step="any" id="portfolioQuantity" class="form-control form-control-sm" placeholder="Cantidad" required></div><div class="col-6"><input type="number" step="any" id="portfolioPrice" class="form-control form-control-sm" placeholder="Precio Compra" required></div><div class="col-12"><button type="submit" class="btn btn-sm btn-info w-100">Añadir a Portafolio</button></div></div></form><form id="alertForm" class="p-2 border rounded bg-body-tertiary small"><label class="form-label fw-bold">Crear Alerta:</label><div class="row g-2 align-items-end"><div class="col-12"><input type="text" id="alertSymbol" class="form-control form-control-sm" placeholder="Símbolo" required></div><div class="col-6"><input type="number" step="0.01" id="alertPrice" class="form-control form-control-sm" placeholder="Precio" required></div><div class="col-6"><select id="alertCondition" class="form-select form-select-sm"><option value="above">>=</option><option value="below"><=</option></select></div><div class="col-12"><button type="submit" class="btn btn-sm btn-warning w-100">Crear Alerta</button></div></div></form></div>`, options: { w: 4, h: 9, minW: 3, minH: 8, id: 'controls' } },
            'drainers': { content: `<div class="widget-header"><h5><i class="fas fa-search-dollar me-2"></i>Análisis de Adelantamientos</h5><div class="widget-controls"><button type="button" class="btn btn-sm btn-danger remove-widget-btn"><i class="fas fa-times"></i></button></div></div><div class="widget-body"><div class="d-flex justify-content-between align-items-center mb-3"><p class="text-muted small mb-0">Detecta eventos anómalos.</p><button id="runAnalysisBtn" class="btn btn-primary"><i class="fas fa-play-circle me-2"></i>Ejecutar Análisis</button></div><div id="drainerAlert" class="alert d-none" role="alert"></div><div class="table-responsive"><table id="drainersTable" class="table table-striped table-hover w-100"></table></div></div>`, options: { w: 12, h: 8, minW: 6, minH: 5, id: 'drainers' } }
        };
    }
    
    loadLayout() {
        const savedLayout = localStorage.getItem('dashboardLayout');
        if (savedLayout && savedLayout !== '[]') {
            const layoutData = JSON.parse(savedLayout);
            this.grid.load(layoutData.map(node => ({...node, content: this.WIDGET_DEFINITIONS[node.id]?.content })));
        } else {
            // --- LAYOUT POR DEFECTO MEJORADO ---
            console.log("Cargando layout por defecto mejorado...");
            this.grid.load([
                 {...this.WIDGET_DEFINITIONS['portfolio'].options, x: 0, y: 0, w: 8, h: 7, content: this.WIDGET_DEFINITIONS['portfolio'].content},
                 {...this.WIDGET_DEFINITIONS['controls'].options, x: 8, y: 0, w: 4, h: 7, content: this.WIDGET_DEFINITIONS['controls'].content},
                 {...this.WIDGET_DEFINITIONS['market-data'].options, x: 0, y: 7, w: 12, h: 7, content: this.WIDGET_DEFINITIONS['market-data'].content},
                 {...this.WIDGET_DEFINITIONS['closing-data'].options, x: 0, y: 14, w: 12, h: 7, content: this.WIDGET_DEFINITIONS['closing-data'].content},
            ]);
        }
        this.setupRemoveButtons();

        setTimeout(() => {
            console.log("Layout listo. Despachando evento 'dashboardReady'.");
            document.dispatchEvent(new Event('dashboardReady'));
            
            // Disparar el evento para los widgets ya cargados en el layout inicial
            this.grid.engine.nodes.forEach(node => {
                document.dispatchEvent(new CustomEvent('widgetAdded', { detail: { element: node.el, widgetId: node.id } }));
            });
        }, 100); 
    }

    saveLayout() {
        const layout = this.grid.save(false);
        localStorage.setItem('dashboardLayout', JSON.stringify(layout));
    }
    
    addWidget(widgetId) {
        const widgetDef = this.WIDGET_DEFINITIONS[widgetId];
        if (!widgetDef || this.grid.engine.nodes.some(n => n.id === widgetId)) return;
        this.grid.addWidget(widgetDef.content, widgetDef.options);
        this.setupRemoveButtons();
    }

    setupRemoveButtons() {
        this.grid.engine.nodes.forEach(node => {
            const removeBtn = node.el.querySelector('.remove-widget-btn');
            if (removeBtn && !removeBtn.listener) {
                removeBtn.listener = true;
                removeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.grid.removeWidget(node.el);
                });
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => { window.dashboardLayout = new DashboardLayout(); });