// src/static/js/controlsManager.js

const controlsManager = {
    isInitialized: false,
    
    init() {
        console.log('[ControlsManager] Módulo en espera de su widget.');
        
        document.addEventListener('widgetAdded', (event) => {
            const widgetElement = event.detail.element;
            if (widgetElement.querySelector('#stockFilterForm')) {
                this.setupWidget(widgetElement);
            }
        });
    },

    setupWidget(widgetElement) {
        if (this.isInitialized) return;
        console.log('[ControlsManager] Widget de Controles detectado. Configurando listeners.');
        
        const stockFilterForm = widgetElement.querySelector('#stockFilterForm');
        const portfolioForm = widgetElement.querySelector('#portfolioForm');
        
        if (stockFilterForm) {
            stockFilterForm.addEventListener('submit', (e) => window.app.handleFilterSubmit(e));
            const clearBtn = stockFilterForm.querySelector('#clearBtn');
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    stockFilterForm.reset();
                    const check = stockFilterForm.querySelector('#allStocksCheck');
                    if(check) check.checked = true;
                    $(stockFilterForm).trigger('submit');
                });
            }
        }

        if (portfolioForm) {
            portfolioForm.addEventListener('submit', (e) => window.portfolioManager.handleAdd(e));
        }
        
        const alertForm = widgetElement.querySelector('#alertForm');
        if (alertForm) {
            // alertForm.addEventListener('submit', ...);
        }
        
        this.isInitialized = true;
    }
};