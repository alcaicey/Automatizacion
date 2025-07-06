// src/static/js/indicadores.js

window.pageOrchestrator = {
    modules: [
        { name: 'financial-kpis', manager: window.kpiManager },
        { name: 'dividends', manager: window.dividendManager }
    ],

    init(uiManager) { // Acepta uiManager
        console.log('[Indicadores] Página cargada. Inicializando módulos...');
        
        this.modules.forEach(module => {
            if (module.manager && typeof module.manager.init === 'function') {
                try {
                    // Pasa uiManager a cada módulo que lo necesite
                    if (module.name === 'dividends') {
                        module.manager.init(uiManager);
                    } else {
                        module.manager.init();
                    }
                    console.log(`[Indicadores] Módulo '${module.name}' inicializado.`);
                } catch (error) {
                    console.error(`Error inicializando el módulo '${module.name}':`, error);
                }
            } else {
                console.warn(`[Indicadores] Módulo '${module.name}' o su método init no fue encontrado.`);
            }
        });
    }
};