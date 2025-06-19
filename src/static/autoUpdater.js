// src/static/js/autoUpdater.js

window.autoUpdater = {
    timerId: null,
    countdownInterval: null,
    ui: null,
    
    init(uiManager) {
        this.ui = uiManager;
        console.log('[AutoUpdater] Módulo inicializado.');
    },

    start(intervalValue, updateCallback) {
        this.stop(); 
        if (intervalValue === "off") return;

        const [min, max] = intervalValue.split('-').map(Number);
        const randomSeconds = Math.floor(Math.random() * (max * 60 - min * 60 + 1)) + (min * 60);
        
        console.log(`[AutoUpdater] Próxima actualización en ${randomSeconds} segundos.`);
        this.startCountdown(randomSeconds);

        this.timerId = setTimeout(() => {
            console.log('[AutoUpdater] Disparando actualización automática.');
            updateCallback(); // Llama a la función que le pasa el orquestador
        }, randomSeconds * 1000);
    },

    stop() {
        if (this.timerId) clearTimeout(this.timerId);
        if (this.countdownInterval) clearInterval(this.countdownInterval);
        this.timerId = null;
        this.countdownInterval = null;
        this.ui.updateCountdown('');
    },

    startCountdown(totalSeconds) {
        let remaining = totalSeconds;
        const update = () => {
            if (remaining <= 0) {
                clearInterval(this.countdownInterval);
                this.ui.updateCountdown('Actualizando...');
                return;
            }
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            this.ui.updateCountdown(`(Próxima en ${minutes}:${seconds < 10 ? '0' : ''}${seconds})`);
            remaining--;
        };
        update();
        this.countdownInterval = setInterval(update, 1000);
    }
};