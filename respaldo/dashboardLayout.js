// src/static/dashboardLayout.js

export default class DashboardLayout {
    constructor(app) {
        this.app = app; // app actúa como widgetManager
        this.grid = null;
        this.widgetList = document.getElementById('widget-list');
        
        // Definiciones de los widgets que necesita el layout por defecto
        this.WIDGET_DEFINITIONS = {
            'portfolio': { grid: { x: 0, y: 0, w: 6, h: 5, id: 'portfolio' } },
            'stock-filter': { grid: { x: 6, y: 0, w: 6, h: 5, id: 'stock-filter' } },
            'news': { grid: { x: 0, y: 5, w: 4, h: 5, id: 'news' } },
            'price-alerts': { grid: { x: 4, y: 5, w: 4, h: 5, id: 'price-alerts' } },
            'bot-status': { grid: { x: 8, y: 5, w: 4, h: 4, id: 'bot-status' } }
        };
        
        // Widgets que se cargarán si no hay un layout guardado
        this.defaultWidgets = [
            { id: 'portfolio' },
            { id: 'stock-filter' },
            { id: 'news' },
            { id: 'price-alerts' },
            { id: 'bot-status' }
        ];
        this.widgetManagers = {
            'bot-status': this.app.botStatusManager,
            'alerts': this.app.alertManager,
            'portfolio': this.app.portfolioManager,
            'closing': this.app.closingManager,
            'news': this.app.newsManager,
            'drainers': this.app.drainerManager,
            'dividends': this.app.dividendManager,
            'kpis': this.app.kpiManager,
        };
        console.log('[Layout] DashboardLayout instanciado.');
    }

    async initialize() {
        console.log('[Layout] 1. Iniciando DashboardLayout.initialize...');
        this.app.uiManager.toggleLoading(true, 'Configurando dashboard...');
        
        try {
            console.log('[Layout] 2. Llamando a initGrid...');
            this.initGrid();
            console.log('[Layout] 4. initGrid completado. Llamando a loadAndRenderWidgets...');
            await this.loadAndRenderWidgets();
            console.log('[Layout] 7. loadAndRenderWidgets completado. Layout inicializado correctamente.');
        } catch (error) {
            console.error('[Layout] ERROR CATASTRÓFICO durante la inicialización del layout:', error);
            this.app.uiManager.showError('No se pudo inicializar el layout del dashboard.');
        } finally {
            console.log('[Layout] 8. Bloque finally alcanzado. Ocultando spinner de carga.');
            this.app.uiManager.toggleLoading(false);
        }
    }

    initGrid() {
        try {
            console.log('[Layout] 3. Dentro de initGrid. Llamando a GridStack.init()...');
            this.grid = GridStack.init({
                cellHeight: 80,
                margin: 10,
                float: true,
                alwaysShowResizeHandle: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
                resizable: { handles: 'e, se, s, sw, w' }
            });
            
            this.setupEventListeners();
            document.dispatchEvent(new CustomEvent('gridstack-ready'));
            console.log('[Layout] 3.1. GridStack inicializado y listeners configurados.');
        } catch (error) {
            console.error('[Layout] Error al inicializar GridStack:', error);
        }
    }

    setupEventListeners() {
        const addWidgetBtnContainer = document.getElementById('addWidgetBtn')?.parentElement;
        if (!addWidgetBtnContainer) return;

        // Escuchar el evento de Bootstrap para mostrar el dropdown
        addWidgetBtnContainer.addEventListener('show.bs.dropdown', this.updateWidgetList.bind(this));

        document.getElementById('widget-list').addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link) {
                e.preventDefault();
                const widgetId = link.getAttribute('data-widget-id');
                if (widgetId && this.app) { // Changed from widgetManager to app
                    this.app.loadWidget(widgetId, true);
                }
            }
        });

        this.grid.on('added', (event, items) => {
            items.forEach(item => {
                const widgetId = item.id;
                if (widgetId) {
                    console.log(`[Layout] GridStack 'added' event for item ${widgetId}. Firing 'widgetAdded'.`);
                    document.dispatchEvent(new CustomEvent('widgetAdded', {
                        detail: { widgetId: widgetId, element: item.el }
                    }));
                }
            });
        });

        this.grid.on('removed', (event, items) => {
            this.saveLayout();
        });

        this.grid.on('change', () => {
            this.saveLayout();
        });
    }

    updateWidgetList() {
        const widgetList = document.getElementById('widget-list');
        if (!widgetList) return;

        widgetList.innerHTML = ''; // Limpiar la lista

        const availableWidgets = this.getAvailableWidgets();
        
        if (availableWidgets.length === 0) {
            const li = document.createElement('li');
            li.innerHTML = `<span class="dropdown-item-text">No hay más widgets para añadir.</span>`;
            widgetList.appendChild(li);
        } else {
            availableWidgets.forEach(widget => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.className = 'dropdown-item';
                a.href = '#';
                a.setAttribute('data-widget-id', widget.id);
                a.textContent = widget.name;
                li.appendChild(a);
                widgetList.appendChild(li);
            });
        }
    }

    getAvailableWidgets() {
        if (!this.app) return []; // Changed from widgetManager to app
        const allWidgets = this.app.getAllWidgetsInfo();
        const activeWidgets = this.getActiveWidgets();
        return allWidgets.filter(widget => !activeWidgets.includes(widget.id));
    }

    getActiveWidgets() {
        return this.grid.engine.nodes.map(node => node.id);
    }

    async loadAndRenderWidgets() {
        console.log("[Layout] 5. Dentro de loadAndRenderWidgets. Buscando layout en localStorage...");
        const savedLayout = localStorage.getItem('dashboardLayout');
        let layoutToLoad = [];

        if (savedLayout) {
            try {
                const parsedLayout = JSON.parse(savedLayout);
                if (Array.isArray(parsedLayout) && parsedLayout.length > 0) {
                    console.log("[Layout] Layout guardado encontrado. Se usarán estos widgets:", parsedLayout.map(w => w.id));
                    layoutToLoad = parsedLayout;
                } else {
                    console.log("[Layout] Layout guardado está vacío. Usando layout por defecto.");
                    layoutToLoad = this.defaultWidgets.map(w => this.WIDGET_DEFINITIONS[w.id].grid);
                }
            } catch (e) {
                console.error("Error al parsear el layout desde localStorage. Se usará el layout por defecto.", e);
                localStorage.removeItem('dashboardLayout');
                layoutToLoad = this.defaultWidgets.map(w => this.WIDGET_DEFINITIONS[w.id].grid);
            }
        } else {
            console.log("[Layout] No se encontró layout guardado. Usando layout por defecto.");
            layoutToLoad = this.defaultWidgets.map(w => this.WIDGET_DEFINITIONS[w.id].grid);
        }

        console.log('[Layout] 5.1. Layout a cargar decidido:', layoutToLoad);

        // Limpiar la cuadrícula antes de añadir nuevos widgets
        this.grid.removeAll();
        
        console.log('[Layout] 6. Iniciando bucle para renderizar widgets...');
        // Renderizar cada widget en el layout
        for (const widgetData of layoutToLoad) {
            console.log(`[Layout] 6.1. Procesando widget: ${widgetData.id}`);
            // La llamada a addWidget ahora solo añade al grid, y el evento 'added' se encargará del resto.
            this.addWidget(widgetData.id, widgetData);
            console.log(`[Layout] 6.2. Widget procesado: ${widgetData.id}`);
        }
        console.log('[Layout] 6.3. Bucle de widgets completado.');
        
        this.updateWidgetList();
    }
    
    // Este método ahora solo se preocupa de AÑADIR un widget al grid
    addWidget(widgetId, layoutOptions = {}) {
        const widgetInfo = this.app.getAllWidgetsInfo().find(w => w.id === widgetId);
        if (!widgetInfo) {
            console.error(`[Layout] Definición no encontrada para el widget: ${widgetId}`);
            return;
        }

        const template = document.getElementById(`${widgetId}Template`);
        if (!template) {
            console.error(`[Layout] Plantilla no encontrada para el widget: ${widgetId}Template`);
            return;
        }

        const widgetContent = template.content.cloneNode(true);
        const widgetEl = document.createElement('div');
        widgetEl.appendChild(widgetContent);

        // Combinar opciones por defecto con las guardadas
        const gridOptions = {
            id: widgetId,
            content: widgetEl.innerHTML,
            ...(this.WIDGET_DEFINITIONS[widgetId]?.grid || {}),
            ...layoutOptions
        };

        this.grid.addWidget(gridOptions);
        console.log(`[Layout] Widget '${widgetId}' añadido al grid.`);

        this.updateWidgetList();
    }

    getWidgetHTML(widgetId) {
        const template = document.getElementById(`${widgetId}Template`);
        if (!template) {
            console.error(`Plantilla no encontrada para el widget: ${widgetId}`);
            return '';
        }
        return template.innerHTML;
    }

    addWidgetToGrid(widgetId, options) {
        console.log(`[Layout] Añadiendo widget al grid: ${widgetId}`);
        const widgetElement = document.getElementById(widgetId);
        
        if (widgetElement && this.grid) {
            // Rellenar el contenido del widget desde su plantilla
            const template = document.getElementById(`${widgetId}Template`);
            if (template) {
                widgetElement.innerHTML = template.innerHTML;
            } else {
                console.error(`[Layout] Template no encontrado para el widget: ${widgetId}Template`);
                return; // No continuar si no hay contenido que mostrar
            }

            this.grid.makeWidget(widgetElement);
            
            // Si hay opciones específicas para este widget (x, y, w, h), aplicarlas
            if(options) {
                this.grid.update(widgetElement, options);
            }
        } else {
            console.warn(`[Layout] Se intentó añadir el widget '${widgetId}' al grid, pero el elemento no se encontró o el grid no está inicializado.`);
        }
    }

    saveLayout() {
        const layout = this.grid.save(false); // `false` para no guardar contenido, solo la estructura
        localStorage.setItem('dashboardLayout', JSON.stringify(layout));
        console.log('[Layout] Layout guardado en localStorage.');
    }
    
    // Función de diagnóstico para la carga de widgets
    verificarCargaWidgets() {
        const widgetsEsperados = this.defaultWidgets.map(w => w.id);
        console.group("[Diagnóstico] Verificación de Widgets");

        widgetsEsperados.forEach(widgetId => {
            const templateId = `${widgetId}Template`;
            const template = document.getElementById(templateId);

            if (!template) {
                console.warn(`⚠️ Template no encontrado: #${templateId}`);
            } else {
                console.log(`✅ Template encontrado: #${templateId}`);
            }

            // Usar `gs-id` que es el atributo que GridStack usa internamente para la identificación del nodo
            const widgetEnGrid = this.grid.engine.nodes.find(node => node.id === widgetId);
            if (!widgetEnGrid) {
                console.warn(`⚠️ Widget "${widgetId}" no fue agregado al grid.`);
            } else {
                console.log(`🟢 Widget "${widgetId}" presente en el grid.`);
            }
        });

        console.groupEnd();
    }

    initWidgets() {
        console.log('[Layout] Inicializando widgets...');
        const widgetElements = document.querySelectorAll('.grid-stack-item');
        console.log(`[Layout] Encontrados ${widgetElements.length} elementos de widget.`);

        widgetElements.forEach(widgetEl => {
            const widgetId = widgetEl.getAttribute('gs-id');
            if (this.widgetManagers[widgetId]) {
                console.log(`[Layout] Inicializando widget: ${widgetId}`);
                this.initializeWidget(this.widgetManagers[widgetId], widgetEl);
            } else {
                console.warn(`[Layout] No se encontró un manager para el widget: ${widgetId}`);
            }
        });
        console.log('[Layout] Todos los widgets procesados.');
    }
    
    initializeWidget(manager, widgetElement) {
        try {
            if (manager && typeof manager.initializeWidget === 'function') {
                manager.initializeWidget(widgetElement);
                console.log(`[Layout] El widget para ${manager.constructor.name} fue inicializado.`);
            } else {
                console.warn(`[Layout] El manager ${manager?.constructor.name || 'desconocido'} no tiene un método initializeWidget.`);
            }
        } catch (error) {
            console.error(`[Layout] Error al inicializar el widget gestionado por ${manager?.constructor.name}:`, error);
            // Opcional: mostrar un error en el propio widget
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger';
            errorDiv.textContent = 'Error al cargar este widget.';
            widgetElement.querySelector('.grid-stack-item-content').innerHTML = '';
            widgetElement.querySelector('.grid-stack-item-content').appendChild(errorDiv);
        }
    }
}