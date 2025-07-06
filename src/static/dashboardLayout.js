// src/static/js/dashboardLayout.js

class DashboardLayout {
    constructor() {
        this.grid = null;
        this.widgetManager = null; // Se establecerá en init
        
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
    }

    init(widgetManager) {
        this.widgetManager = widgetManager;
        // Esperar a que el DOM esté completamente cargado
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', this._initializeGrid.bind(this));
        } else {
            this._initializeGrid();
        }
    }

    _initializeGrid() {
        this.grid = GridStack.init({
            cellHeight: 'auto',
            margin: 10,
            float: true,
            alwaysShowResizeHandle: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
            resizable: { handles: 'e, se, s, sw, w' }
        });
        
        this.loadLayout();
        this.setupEventListeners();
        document.dispatchEvent(new CustomEvent('gridstack-ready'));
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
                if (widgetId && this.widgetManager) {
                    this.widgetManager.loadWidget(widgetId, true);
                }
            }
        });

        this.grid.on('added', (event, items) => {
            items.forEach(item => {
                const widgetId = item.id || item.el.querySelector('[data-widget-id]')?.dataset.widgetId;
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
        if (!this.widgetManager) return [];
        const allWidgets = this.widgetManager.getAllWidgetsInfo();
        const activeWidgets = this.getActiveWidgets();
        return allWidgets.filter(widget => !activeWidgets.includes(widget.id));
    }

    getActiveWidgets() {
        return this.grid.engine.nodes.map(node => node.id);
    }

    loadLayout() {
        const savedLayout = localStorage.getItem('dashboardLayout');
        if (savedLayout) {
            try {
                const layout = JSON.parse(savedLayout);
                // Asegurarse de que el layout no esté vacío y sea un array
                if (Array.isArray(layout) && layout.length > 0) {
                    this.grid.load(layout);
                    return; // Salir para no cargar el layout por defecto
                }
            } catch (e) {
                console.error("Error al cargar el layout desde localStorage. Se usará el layout por defecto.", e);
                localStorage.removeItem('dashboardLayout'); // Limpiar el layout corrupto
            }
        }
        this.loadDefaultLayout();
    }

    loadDefaultLayout() {
        console.log("Cargando layout por defecto.");
        this.defaultWidgets.forEach(widget => {
            this.addWidget(widget.id);
        });
    }

    addWidget(widgetId) {
        const widgetDef = this.WIDGET_DEFINITIONS[widgetId];
        if (widgetDef) {
            this.addWidgetToGrid(widgetId, widgetDef.grid);
        } else {
            console.warn(`No se encontró la definición para el widget: ${widgetId}`);
        }
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
            console.warn(`Se intentó añadir el widget '${widgetId}' al grid, pero el elemento no se encontró.`);
        }
    }

    saveLayout() {
        const layout = this.grid.save();
        localStorage.setItem('dashboardLayout', JSON.stringify(layout));
    }
}

export default DashboardLayout;