async function loadLogs() {
    const resp = await fetch('/api/logs');
    const data = await resp.json();
    const tbody = document.querySelector('#logsTable tbody');
    tbody.innerHTML = '';
    for (const log of data) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${log.id}</td>
            <td>${log.timestamp}</td>
            <td>${log.action}</td>
            <td>${log.message}</td>
            <td><button class="btn btn-sm btn-danger" data-id="${log.id}">Borrar</button></td>
        `;
        tbody.appendChild(tr);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadLogs();
    document.querySelector('#searchInput').addEventListener('input', async (e) => {
        const q = e.target.value;
        const resp = await fetch('/api/logs?q=' + encodeURIComponent(q));
        const data = await resp.json();
        const tbody = document.querySelector('#logsTable tbody');
        tbody.innerHTML = '';
        for (const log of data) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${log.id}</td>
                <td>${log.timestamp}</td>
                <td>${log.action}</td>
                <td>${log.message}</td>
                <td><button class="btn btn-sm btn-danger" data-id="${log.id}">Borrar</button></td>
            `;
            tbody.appendChild(tr);
        }
    });
    document.querySelector('#logsTable').addEventListener('click', async (e) => {
        if (e.target.matches('button[data-id]')) {
            const id = e.target.getAttribute('data-id');
            await fetch('/api/logs/' + id, {method: 'DELETE'});
            loadLogs();
        }
    });
});
