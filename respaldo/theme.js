export default class Theme {
    constructor(app) {
        this.app = app;
        this.themeDropdown = document.getElementById('themeDropdown');
        this.themeButtons = document.querySelectorAll('.dropdown-item[data-theme-value]');
    }

    initialize() {
        this.applyTheme(this.getStoredTheme());
        this.addEventListeners();
    }

    getStoredTheme() {
        return localStorage.getItem('theme') || 'light';
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);

        const activeThemeItem = document.querySelector(`.dropdown-item[data-theme-value="${theme}"]`);
        if (this.themeDropdown && activeThemeItem) {
            this.themeDropdown.innerHTML = activeThemeItem.innerHTML;
        }
    }

    addEventListeners() {
        this.themeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const selectedTheme = button.getAttribute('data-theme-value');
                this.applyTheme(selectedTheme);
            });
        });
    }
}
