// src/static/js/utils/autoUpdater.js

export default class AutoUpdater {
    constructor(app) {
        this.app = app;
        this.intervalId = null;
        this.selectElement = document.getElementById('auto-update-select');
    }

    initialize() {
        if (!this.selectElement) return;

        // Recuperar y aplicar el valor guardado en sessionStorage
        const savedInterval = sessionStorage.getItem('autoUpdateInterval');
        if (savedInterval) {
            this.selectElement.value = savedInterval;
            this.start(parseInt(savedInterval, 10));
        }
        
        this.selectElement.addEventListener('change', (e) => {
            const minutes = parseInt(e.target.value, 10);
            sessionStorage.setItem('autoUpdateInterval', minutes); // Guardar selección
            this.start(minutes);
        });
        console.log("[AutoUpdater] Inicializado.");
    }

    start(minutes) {
        this.stop();
        if (minutes > 0) {
            const milliseconds = minutes * 60 * 1000;
            this.intervalId = setInterval(() => {
                // Aquí iría la lógica de actualización
                console.log(`Auto-actualización ejecutada cada ${minutes} minutos.`);
                this.app.eventHandlers.handleUpdateClick();
            }, milliseconds);
            console.log(`Auto-actualización iniciada cada ${minutes} minutos.`);
        }
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('Auto-actualización detenida.');
        }
    }
}