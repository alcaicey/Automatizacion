document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/credentials')
        .then(r => r.json())
        .then(data => {
            if (data.has_credentials) {
                window.location.href = '/index.html';
            }
        });

    const form = document.getElementById('loginForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const remember = document.getElementById('remember').checked;
        const resp = await fetch('/api/credentials', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, remember })
        });
        if (resp.ok) {
            window.location.href = '/index.html';
        } else {
            alert('Error al guardar credenciales');
        }
    });
});
