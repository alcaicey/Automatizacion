$(document).ready(function() {
    const table = new Tabulator("#logs-table", {
        height: "80vh",
        layout: "fitColumns",
        placeholder: "No hay logs disponibles",
        ajaxURL: '/api/system/logs',
        ajaxConfig: "GET",
        ajaxResponse: function(url, params, response) {
            // Asume que la respuesta ya es el array de logs
        },
        columns: [
            { data: 'id', title: 'ID' },
            { data: 'timestamp', title: 'Fecha' },
            { data: 'action', title: 'Acción/Fuente' },
            { data: 'message', title: 'Mensaje' },
            {
                data: null,
                title: '',
                orderable: false,
                searchable: false,
                render: function(data, type, row) {
                    return `<button class="btn btn-sm btn-danger delete-btn" data-id="${row.id}">Borrar</button>`;
                }
            }
        ],
        order: [[1, 'desc']], // Ordenar por fecha descendente por defecto
        responsive: true,
        language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json' },
        dom: 'frtip' // Layout simple: filtro y paginación
    });

    // Conectar el input de búsqueda personalizado con el buscador de DataTables
    $('#searchInput').on('keyup', function() {
        table.search(this.value).draw();
    });

    // Manejador de eventos delegado para los botones de borrado
    $('#logsTable tbody').on('click', '.delete-btn', async function() {
        const id = $(this).data('id');
        if (confirm(`¿Estás seguro de que quieres borrar el log con ID ${id}?`)) {
            await fetch('/api/system/logs/' + id, { method: 'DELETE' });
            table.ajax.reload(null, false); // Recargar datos sin resetear la paginación
        }
    });

    async function deleteLog(id) {
        if (!confirm('¿Estás seguro de que quieres eliminar este log?')) return;
        await fetch('/api/system/logs/' + id, { method: 'DELETE' });
        table.replaceData(); // Recargar la tabla
    }

    document.getElementById('delete-all-logs').addEventListener('click', async () => {
        if (!confirm('¿Estás seguro de que quieres eliminar TODOS los logs?')) return;
        await fetch('/api/system/logs', { method: 'DELETE' });
        table.replaceData();
    });

});