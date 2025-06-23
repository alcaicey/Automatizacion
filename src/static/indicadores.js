// src/static/js/indicadores.js

document.addEventListener('DOMContentLoaded', () => {
    console.log('[Indicadores] Página cargada. Inicializando módulos...');

    // Un objeto para mantener todos los gestores de módulos.
    const indicatorModules = {
        dividends: window.dividendManager,
        'financial-kpis': window.kpiManager,
    };

    // Inicializa cada módulo que encuentre en la página.
    for (const moduleName in indicatorModules) {
        if (document.getElementById(`module-${moduleName}`)) {
            const manager = indicatorModules[moduleName];
            if (manager && typeof manager.init === 'function') {
                try {
                    manager.init();
                    console.log(`[Indicadores] Módulo '${moduleName}' inicializado.`);
                } catch (error) {
                    console.error(`[Indicadores] Error al inicializar el módulo '${moduleName}':`, error);
                }
            }
        }
    }
});