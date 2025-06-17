document.addEventListener('DOMContentLoaded', () => {
    const tableSelect = document.getElementById('tableSelect');
    const recordsTable = document.getElementById('recordsTable');
    const addBtn = document.getElementById('addRecordBtn');
    const modalEl = document.getElementById('recordModal');
    const modal = new bootstrap.Modal(modalEl);
    const formBody = document.getElementById('recordFormBody');
    const form = document.getElementById('recordForm');

    let currentTable = null;
    let currentData = [];

    async function loadModels() {
        const res = await fetch('/api/mantenedores/models');
        const models = await res.json();
        tableSelect.innerHTML = '<option value="">Seleccione...</option>' +
            models.map(m => `<option value="${m}">${m}</option>`).join('');
    }

    async function loadTable(name) {
        const res = await fetch(`/api/mantenedores/${name}`);
        currentData = await res.json();
        renderTable();
    }

    function renderTable() {
        recordsTable.innerHTML = '';
        if (!currentData || currentData.length === 0) {
            recordsTable.innerHTML = '<tr><td>No hay datos</td></tr>';
            return;
        }
        const headings = Object.keys(currentData[0]);
        const thead = document.createElement('thead');
        thead.className = 'table-dark';
        thead.innerHTML = '<tr>' + headings.map(h => `<th>${h}</th>`).join('') + '<th></th></tr>';
        const tbody = document.createElement('tbody');
        currentData.forEach((row, idx) => {
            const cells = headings.map(h => `<td>${row[h] ?? ''}</td>`).join('');
            tbody.innerHTML += `<tr data-idx="${idx}">${cells}<td><button class="btn btn-sm btn-warning edit-btn">Editar</button> <button class="btn btn-sm btn-danger delete-btn">Borrar</button></td></tr>`;
        });
        recordsTable.appendChild(thead);
        recordsTable.appendChild(tbody);
    }

    function openForm(data = {}) {
        const columns = Object.keys(currentData[0] || data);
        form.dataset.id = data.id || '';
        formBody.innerHTML = '';
        columns.forEach(col => {
            if (col === 'id') return;
            const value = data[col] ?? '';
            formBody.innerHTML += `<div class="mb-3"><label class="form-label">${col}</label><input class="form-control" name="${col}" value="${value}"></div>`;
        });
        modal.show();
    }

    tableSelect.addEventListener('change', () => {
        currentTable = tableSelect.value;
        if (currentTable) loadTable(currentTable);
    });

    addBtn.addEventListener('click', () => openForm());

    recordsTable.addEventListener('click', async (e) => {
        const tr = e.target.closest('tr');
        if (!tr) return;
        const idx = tr.dataset.idx;
        if (e.target.classList.contains('edit-btn')) {
            openForm(currentData[idx]);
        } else if (e.target.classList.contains('delete-btn')) {
            if (confirm('¿Borrar registro?')) {
                const id = currentData[idx].id;
                await fetch(`/api/mantenedores/${currentTable}/${id}`, { method: 'DELETE' });
                loadTable(currentTable);
            }
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(form).entries());
        const id = form.dataset.id;
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/mantenedores/${currentTable}/${id}` : `/api/mantenedores/${currentTable}`;
        await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        modal.hide();
        loadTable(currentTable);
    });

    loadModels();
});
