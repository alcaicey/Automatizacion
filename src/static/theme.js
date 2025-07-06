function applyTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('theme', theme);

    // Actualizar el texto del botón principal del dropdown para reflejar el tema activo
    const themeDropdown = document.getElementById('themeDropdown');
    const activeThemeItem = document.querySelector(`.dropdown-item[data-theme-value="${theme}"]`);
    if (themeDropdown && activeThemeItem) {
        themeDropdown.innerHTML = `${activeThemeItem.innerHTML}`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Aplicar tema guardado al cargar
    const storedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(storedTheme);

    // Añadir listeners a los botones del dropdown
    const themeButtons = document.querySelectorAll('.dropdown-item[data-theme-value]');
    themeButtons.forEach(button => {
        button.addEventListener('click', () => {
            const selectedTheme = button.getAttribute('data-theme-value');
            applyTheme(selectedTheme);
        });
    });
});
