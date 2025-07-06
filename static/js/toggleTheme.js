document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('themeToggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.className = currentTheme;
    
    themeToggle.addEventListener('click', () => {
        const newTheme = document.documentElement.className === 'light' ? 'dark' : 'light';
        document.documentElement.className = newTheme;
        localStorage.setItem('theme', newTheme);
    });
});
