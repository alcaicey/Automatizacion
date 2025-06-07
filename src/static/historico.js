// CRUD operations for stock_prices

document.addEventListener('DOMContentLoaded', () => {
    loadPrices();

    const form = document.getElementById('priceForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = form.dataset.id;
        const data = {
            symbol: form.symbol.value,
            price: parseFloat(form.price.value || 0),
            variation: parseFloat(form.variation.value || 0),
            timestamp: form.timestamp.value
        };
        let url = '/api/prices';
        let method = 'POST';
        if (id) {
            url += `/${id}`;
            method = 'PUT';
        }
        await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        form.reset();
        delete form.dataset.id;
        loadPrices();
    });
});

async function loadPrices() {
    const tbody = document.querySelector('#pricesTable tbody');
    tbody.innerHTML = '';
    const res = await fetch('/api/prices?limit=100');
    const data = await res.json();
    data.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.id}</td>
            <td>${p.symbol}</td>
            <td>${p.price}</td>
            <td>${p.variation ?? ''}</td>
            <td>${p.timestamp}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editPrice(${p.id})">Editar</button>
                <button class="btn btn-sm btn-danger" onclick="deletePrice(${p.id})">Eliminar</button>
            </td>`;
        tbody.appendChild(tr);
    });
}

async function editPrice(id) {
    const res = await fetch(`/api/prices/${id}`);
    const data = await res.json();
    const form = document.getElementById('priceForm');
    form.symbol.value = data.symbol;
    form.price.value = data.price;
    form.variation.value = data.variation ?? '';
    form.timestamp.value = data.timestamp.slice(0,19);
    form.dataset.id = data.id;
}

async function deletePrice(id) {
    await fetch(`/api/prices/${id}`, { method: 'DELETE' });
    loadPrices();
}
