function applyTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('theme', theme);
}

document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;
    const stored = localStorage.getItem('theme') || 'light';
    applyTheme(stored);
    toggle.innerHTML =
        stored === 'dark'
            ? '☀️ Modo Claro'
            : '🌙 Modo Oscuro';
    toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-bs-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        toggle.innerHTML =
            next === 'dark'
                ? '☀️ Modo Claro'
                : '🌙 Modo Oscuro';
    });
});
