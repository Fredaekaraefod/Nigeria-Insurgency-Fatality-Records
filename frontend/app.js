document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const dataTableBody = document.getElementById('dataTableBody');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');

    let searchTimeout = null;
    let myChart = null;

    async function fetchIncidents(query = '') {
        loadingIndicator.style.display = 'block';
        errorMessage.style.display = 'none';
        dataTableBody.innerHTML = '';

        try {
            const url = query ? `/api/incidents?q=${encodeURIComponent(query)}` : '/api/incidents';
            const response = await fetch(url);
            const data = await response.json();

            if (data.success) {
                renderTable(data.data);
                renderChart(data.data);
            } else {
                showError(data.error);
            }
        } catch (err) {
            showError('Could not connect to the backend server. Is it running?');
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }

    function renderTable(rows) {
        if (!rows || rows.length === 0) {
            dataTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">No incidents found matching your query.</td></tr>';
            return;
        }

        rows.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${escapeHTML(row.date)}</td>
                <td>${escapeHTML(row.state)}</td>
                <td>${escapeHTML(row.location)}</td>
                <td>${escapeHTML(row.attack_type)}</td>
                <td>${escapeHTML(row.fatalities || '0')}</td>
                <td class="summary-cell" title="${escapeHTML(row.summary)}">${escapeHTML(row.summary)}</td>
            `;
            dataTableBody.appendChild(tr);
        });
    }

    function renderChart(rows) {
        const chartWrapper = document.getElementById('chartWrapper');
        if (!rows || rows.length === 0) {
            chartWrapper.style.display = 'none';
            return;
        }
        
        chartWrapper.style.display = 'block';

        // Aggregate data by Attack Type
        const attackCounts = {};
        rows.forEach(row => {
            const type = row.attack_type || 'Unknown';
            attackCounts[type] = (attackCounts[type] || 0) + 1;
        });

        const labels = Object.keys(attackCounts);
        const data = Object.values(attackCounts);

        if (myChart) {
            myChart.destroy();
        }

        const ctx = document.getElementById('dataChart').getContext('2d');
        myChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Incidents by Attack Type',
                    data: data,
                    backgroundColor: 'rgba(59, 130, 246, 0.6)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { color: '#d1d5db', font: { family: 'Inter' } }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#9ca3af', stepSize: 1 },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.style.display = 'block';
    }

    function escapeHTML(str) {
        if (!str) return '';
        return str.toString()
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Initial load
    fetchIncidents();

    // Search input event listener with debounce
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            fetchIncidents(e.target.value.trim());
        }, 300); // 300ms debounce
    });
});
