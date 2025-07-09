// src/static/theme.modular.js

export class ThemeManager {
    constructor() {
        // En el futuro, podría tener más lógica, como manejar el botón de toggle
    }

    applyTheme(theme) {
        if (document.documentElement) {
            document.documentElement.setAttribute('data-bs-theme', theme);
        }
    }
} 