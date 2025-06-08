async function logErrorToServer(message, stack = '', action = '') {
    try {
        await fetch('/api/logs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, stack, action })
        });
    } catch (e) {
        console.error('Error enviando log al servidor:', e);
    }
}

window.addEventListener('error', (e) => {
    logErrorToServer(e.message || 'Error', e.error ? e.error.stack : '', 'global');
});

window.addEventListener('unhandledrejection', (e) => {
    const reason = e.reason || {};
    logErrorToServer(reason.message || String(reason), reason.stack, 'global');
});

document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/credentials')
        .then(r => r.json())
        .then(data => {
            if (data.has_credentials) {
                window.location.href = '/index.html';
            }
        })
        .catch(err => {
            console.error('Error cargando credenciales:', err);
            logErrorToServer(err.message, err.stack, 'loadCredentials');
        });

    const form = document.getElementById('loginForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const remember = document.getElementById('remember').checked;
        try {
            const resp = await fetch('/api/credentials', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, remember })
            });
            if (resp.ok) {
                window.location.href = '/index.html';
            } else {
                alert('Error al guardar credenciales');
                logErrorToServer('Error al guardar credenciales', '', 'loginSubmit');
            }
        } catch (err) {
            alert('Error al guardar credenciales');
            console.error('Error al enviar credenciales:', err);
            logErrorToServer(err.message, err.stack, 'loginSubmit');
        }
    });
});
