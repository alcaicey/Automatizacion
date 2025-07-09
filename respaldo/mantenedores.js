$(document).ready(function() {
    const tableSelect = document.getElementById('tableSelect');
    const recordsTableContainer = document.getElementById('recordsTableContainer');
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
    let recordsDataTable = null;
    let pkColumns = [];
    let allRecords = [];

    const createGenericRenderer = () => (data, type, row) => {
        if (type === 'display') {
            if (typeof data === 'number') {
                const colorClass = data > 0 ? 'text-success' : (data < 0 ? 'text-danger' : 'text-muted');
                return `<span class="fw-bold ${colorClass}">${data.toLocaleString('es-CL')}</span>`;
            }
            if (typeof data === 'string' && data.length > 70) return `<span title="${data}">${data.substring(0, 70)}...</span>`;
        }
        return data;
    };

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

    async function loadTable(name) {
        currentTable = name;
        try {
            // Se asume que la API puede devolver todos los registros para tablas de mantenedores.
            // Si las tablas son muy grandes, se necesitaría server-side processing.
            const res = await fetch(`/api/mantenedores/${name}?per_page=10000`);
            if (!res.ok) throw new Error(`Error al cargar datos de '${name}'.`);
            
            const responseData = await res.json();
            pkColumns = responseData.pk_columns || [];
            allRecords = responseData.records || [];
            
            renderDataTable(allRecords);
        } catch (error) {
            alert(error.message);
        }
    }

    function renderDataTable(records) {
        if (recordsDataTable) {
            recordsDataTable.destroy();
        }
        recordsTableContainer.innerHTML = '<table id="recordsTable" class="table table-striped table-bordered table-hover w-100"></table>';
        
        if (!records || records.length === 0) {
            recordsTableContainer.innerHTML = '<div class="alert alert-warning">No hay datos para mostrar.</div>';
            recordCounter.textContent = '0 registros.';
            return;
        }

        const headings = Object.keys(records[0]);
        const dtColumns = headings.map(h => ({
            data: h,
            title: h.replace(/_/g, ' '),
            render: createGenericRenderer()
        }));
        dtColumns.push({
            data: null,
            title: 'Acciones',
            orderable: false,
            searchable: false,
            render: () => `<button class="btn btn-sm btn-warning edit-btn">Editar</button> <button class="btn btn-sm btn-danger delete-btn">Borrar</button>`
        });

        recordsDataTable = $('#recordsTable').DataTable({
            data: records,
            columns: dtColumns,
            responsive: true,
            language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
            "initComplete": function(settings, json) {
                recordCounter.textContent = `${settings.fnRecordsDisplay()} de ${settings.fnRecordsTotal()} registros.`;
            },
            "drawCallback": function(settings) {
                 recordCounter.textContent = `${settings.fnRecordsDisplay()} de ${settings.fnRecordsTotal()} registros.`;
            }
        });
    }

    function openForm(data = null) {
        const isEditing = data !== null;
        modalTitle.textContent = isEditing ? `Editar Registro en ${currentTable}` : `Añadir Registro a ${currentTable}`;
        
        const columns = allRecords.length > 0 ? Object.keys(allRecords[0]) : (data ? Object.keys(data) : []);
        
        form.dataset.id = isEditing ? getRecordId(data) : '';
        formBody.innerHTML = '';
        columns.forEach(col => {
            const isPk = pkColumns.includes(col);
            let value = data ? (data[col] ?? '') : '';
            // Formatear fechas para el input si es necesario
            if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)) {
                value = value.substring(0, 16); // Formato YYYY-MM-DDTHH:MM
            }
            const inputType = typeof value === 'number' ? 'number' : 'text';
            formBody.innerHTML += `
                <div class="mb-3">
                    <label class="form-label">${col}</label>
                    <input type="${inputType}" class="form-control" name="${col}" value="${value}" ${isEditing && isPk ? 'readonly' : ''}>
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
            loadTable(currentTable);
        } else {
            addBtn.style.display = 'none';
            searchContainer.style.display = 'none';
            deleteAllBtn.style.display = 'none';
            recordsTableContainer.innerHTML = '';
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
        if(recordsDataTable) {
            recordsDataTable.search(searchInput.value).draw();
        }
    });

    $('#recordsTableContainer').on('click', '.edit-btn, .delete-btn', async function() {
        const tr = $(this).closest('tr');
        const rowData = recordsDataTable.row(tr).data();
        if (!rowData) return;
        
        const recordId = getRecordId(rowData);

        if ($(this).hasClass('edit-btn')) {
            openForm(rowData);
        } else if ($(this).hasClass('delete-btn')) {
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

    loadModels();
});