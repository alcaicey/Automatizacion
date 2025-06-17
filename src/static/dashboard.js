// src/static/dashboard.js

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('symbolInput');
    const btn = document.getElementById('plotBtn');
    const ctx = document.getElementById('priceChart').getContext('2d');
    let chart = null;

    async function loadHistory(symbol) {
        const res = await fetch(`/api/stocks/history/${encodeURIComponent(symbol)}`);
        if (!res.ok) throw new Error('Error al obtener datos');
        return res.json();
    }

    async function plot(symbol) {
        const data = await loadHistory(symbol);
        if (chart) {
            chart.data.labels = data.labels;
            chart.data.datasets[0].data = data.data;
            chart.data.datasets[0].label = symbol;
            chart.update();
            return;
        }
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: symbol,
                    data: data.data,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                }]
            },
            options: { responsive: true }
        });
    }

    btn.addEventListener('click', () => {
        const symbol = input.value.trim().toUpperCase();
        if (symbol) plot(symbol);
    });

    const socket = io();
    socket.on('new_data', () => {
        const symbol = input.value.trim().toUpperCase();
        if (symbol) plot(symbol);
    });
});
