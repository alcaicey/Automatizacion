document.addEventListener('DOMContentLoaded', () => {
    const tableSelect = document.getElementById('tableSelect');
    const recordsTableContainer = document.getElementById('recordsTableContainer');
    const paginationContainer = document.getElementById('paginationContainer');
    const recordCounter = document.getElementById('recordCounter');
    const searchContainer = document.getElementById('searchContainer');
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const addBtn = document.getElementById('addRecordBtn');
    const deleteAllBtn = document.getElementById('deleteAllBtn');
    const modalEl = document.getElementById('recordModal');
    const modal = new bootstrap.Modal(modalEl);
    const form = document.getElementById('recordForm');
    const formBody = document.getElementById('recordFormBody');
    const modalTitle = document.getElementById('recordModalLabel');

    let currentTable = null;
    let currentData = [];
    let pkColumns = [];
    let currentSearchTerm = '';
    
    const allowedForMassDelete = ['log_entries', 'stock_prices'];

    function getRecordId(row) {
        if (pkColumns.length === 1) {
            return row[pkColumns[0]];
        }
        const idParts = pkColumns.map(col => row[col]);
        return JSON.stringify(idParts);
    }

    async function loadModels() {
        try {
            const res = await fetch('/api/mantenedores/models');
            if (!res.ok) throw new Error('No se pudieron cargar los modelos.');
            const models = await res.json();
            tableSelect.innerHTML = '<option value="">Seleccione una tabla...</option>' +
                models.map(m => `<option value="${m}">${m.replace(/_/g, ' ')}</option>`).join('');
        } catch (error) {
            alert(error.message);
        }
    }

    async function loadTable(name, page = 1, searchTerm = '') {
        currentTable = name;
        currentSearchTerm = searchTerm;
        try {
            const params = new URLSearchParams({ page, per_page: 50 });
            if (searchTerm) {
                params.append('q', searchTerm);
            }
            const res = await fetch(`/api/mantenedores/${name}?${params.toString()}`);
            if (!res.ok) throw new Error(`Error al cargar datos de '${name}'.`);
            
            const responseData = await res.json();
            pkColumns = responseData.pk_columns || [];
            currentData = responseData.records || [];
            
            renderTable(currentData);
            renderPagination(responseData.pagination);
            recordCounter.textContent = `Mostrando ${currentData.length} de ${responseData.pagination.total_records} registros.`;
        } catch (error) {
            alert(error.message);
        }
    }

    function renderTable(records) {
        recordsTableContainer.innerHTML = '<table id="recordsTable" class="table table-striped table-bordered table-hover w-100"></table>';
        const recordsTable = document.getElementById('recordsTable');
        
        if (!records || records.length === 0) {
            recordsTable.innerHTML = '<thead><tr><th>Mensaje</th></tr></thead><tbody><tr><td>No hay datos para mostrar.</td></tr></tbody>';
            return;
        }

        const headings = Object.keys(records[0]);
        const thead = document.createElement('thead');
        thead.innerHTML = '<tr>' + headings.map(h => `<th>${h}</th>`).join('') + '<th>Acciones</th></tr>';
        
        const tbody = document.createElement('tbody');
        records.forEach(row => {
            const tr = document.createElement('tr');
            tr.dataset.id = getRecordId(row);
            
            let cells = '';
            headings.forEach(h => {
                let value = row[h];
                if (typeof value === 'string' && value.length > 50) value = value.substring(0, 50) + '...';
                cells += `<td>${value ?? ''}</td>`;
            });
            
            cells += `<td><button class="btn btn-sm btn-warning edit-btn">Editar</button> <button class="btn btn-sm btn-danger delete-btn">Borrar</button></td>`;
            tr.innerHTML = cells;
            tbody.appendChild(tr);
        });

        recordsTable.appendChild(thead);
        recordsTable.appendChild(tbody);
    }

    function renderPagination(pagination) {
        paginationContainer.innerHTML = '';
        if (!pagination || pagination.total_pages <= 1) return;

        let html = '<nav><ul class="pagination">';
        html += `<li class="page-item ${pagination.has_prev ? '' : 'disabled'}"><a class="page-link" href="#" data-page="${pagination.current_page - 1}">Anterior</a></li>`;
        
        const startPage = Math.max(1, pagination.current_page - 2);
        const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);
        
        if (startPage > 1) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        for (let i = startPage; i <= endPage; i++) {
            html += `<li class="page-item ${i === pagination.current_page ? 'active' : ''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
        if (endPage < pagination.total_pages) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        html += `<li class="page-item ${pagination.has_next ? '' : 'disabled'}"><a class="page-link" href="#" data-page="${pagination.current_page + 1}">Siguiente</a></li>`;
        html += '</ul></nav>';
        paginationContainer.innerHTML = html;
    }

    function openForm(data = null) {
        const isEditing = data !== null;
        modalTitle.textContent = isEditing ? `Editar Registro en ${currentTable}` : `Añadir Registro a ${currentTable}`;
        
        const columns = currentData.length > 0 ? Object.keys(currentData[0]) : (data ? Object.keys(data) : []);
        
        form.dataset.id = isEditing ? getRecordId(data) : '';
        formBody.innerHTML = '';
        columns.forEach(col => {
            const isPk = pkColumns.includes(col);
            const value = data ? (data[col] ?? '') : '';
            formBody.innerHTML += `
                <div class="mb-3">
                    <label class="form-label">${col}</label>
                    <input class="form-control" name="${col}" value="${value}" ${isEditing && isPk ? 'readonly' : ''}>
                </div>`;
        });
        modal.show();
    }

    tableSelect.addEventListener('change', () => {
        currentTable = tableSelect.value;
        searchInput.value = '';
        if (currentTable) {
            addBtn.style.display = 'inline-block';
            searchContainer.style.display = 'block';
            deleteAllBtn.style.display = allowedForMassDelete.includes(currentTable) ? 'inline-block' : 'none';
            loadTable(currentTable, 1);
        } else {
            addBtn.style.display = 'none';
            searchContainer.style.display = 'none';
            deleteAllBtn.style.display = 'none';
            recordsTableContainer.innerHTML = '';
            paginationContainer.innerHTML = '';
            recordCounter.textContent = '';
        }
    });

    addBtn.addEventListener('click', () => {
        if (!currentTable) return;
        openForm();
    });

    deleteAllBtn.addEventListener('click', async () => {
        if (!currentTable || !allowedForMassDelete.includes(currentTable)) return;
        if (confirm(`¿Estás SEGURO de que quieres borrar TODOS los registros de la tabla '${currentTable}'? Esta acción no se puede deshacer.`)) {
            try {
                const res = await fetch(`/api/mantenedores/${currentTable}/all`, { method: 'DELETE' });
                const result = await res.json();
                if (res.ok) {
                    alert(result.message);
                    loadTable(currentTable);
                } else {
                    throw new Error(result.description || 'Error desconocido.');
                }
            } catch (error) {
                alert(`Error al borrar los registros: ${error.message}`);
            }
        }
    });
    
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        loadTable(currentTable, 1, searchInput.value);
    });

    recordsTableContainer.addEventListener('click', async (e) => {
        const recordRow = e.target.closest('tr');
        if (!recordRow) return;
        
        const recordId = recordRow.dataset.id;
        const recordData = currentData.find(row => getRecordId(row) == recordId);

        if (e.target.classList.contains('edit-btn')) {
            openForm(recordData);
        } else if (e.target.classList.contains('delete-btn')) {
            if (confirm(`¿Borrar registro con ID ${recordId}?`)) {
                const url = `/api/mantenedores/${currentTable}/${encodeURIComponent(recordId)}`;
                await fetch(url, { method: 'DELETE' });
                loadTable(currentTable);
            }
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            if (!isNaN(value) && value.trim() !== '' && !key.includes('date')) {
                data[key] = Number(value);
            } else {
                data[key] = value;
            }
        }
        const id = form.dataset.id;
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/mantenedores/${currentTable}/${encodeURIComponent(id)}` : `/api/mantenedores/${currentTable}`;
        
        const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        if (res.ok) {
            modal.hide();
            loadTable(currentTable);
        } else {
            const error = await res.json();
            alert(`Error: ${error.description || 'Ocurrió un error.'}`);
        }
    });
    
    paginationContainer.addEventListener('click', (e) => {
        e.preventDefault();
        if (e.target.tagName === 'A' && e.target.dataset.page) {
            const page = parseInt(e.target.dataset.page, 10);
            if (page) {
                loadTable(currentTable, page, currentSearchTerm);
            }
        }
    });

    loadModels();
});