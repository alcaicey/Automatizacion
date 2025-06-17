// src/static/alerts.js

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('alertForm');
    const socket = io();

    function showStatus(message, type = 'info') {
        const el = document.getElementById('statusMessage');
        if (!el) return;
        const icons = { info: 'info-circle', success: 'check-circle', warning: 'exclamation-triangle', danger: 'x-circle' };
        el.innerHTML = `<i class="fas fa-${icons[type]} me-2"></i><span>${message}</span>`;
        el.className = `alert alert-${type} small py-2`;
    }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const symbol = document.getElementById('alertSymbol').value.trim().toUpperCase();
            const price = parseFloat(document.getElementById('alertPrice').value);
            const condition = document.getElementById('alertCondition').value;
            if (!symbol || isNaN(price)) { showStatus('Datos inválidos', 'danger'); return; }
            try {
                const res = await fetch('/api/alerts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbol, target_price: price, condition })
                });
                if (!res.ok) throw new Error('Error al crear alerta');
                form.reset();
                showStatus('Alerta creada', 'success');
            } catch (err) {
                showStatus(err.message, 'danger');
            }
        });
    }

    socket.on('alert_triggered', (data) => {
        showStatus(data.message, 'warning');
    });
});
