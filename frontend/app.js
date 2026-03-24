document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const dataTableBody = document.getElementById('dataTableBody');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');

    let searchTimeout = null;
    let typeChartInstance = null;
    let timeChartInstance = null;

    Chart.defaults.color = '#9ca3af';
    Chart.defaults.font.family = 'Inter';

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
                renderCharts(data.data);
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

    function renderCharts(rows) {
        const chartsRow = document.getElementById('chartsRow');
        if (!rows || rows.length === 0) {
            chartsRow.style.display = 'none';
            return;
        }
        
        chartsRow.style.display = 'grid';

        // 1. Process data for Doughnut Chart (Attack Types)
        const typeCounts = {};
        rows.forEach(r => {
            const type = r.attack_type || 'Unknown';
            typeCounts[type] = (typeCounts[type] || 0) + 1;
        });

        const typeLabels = Object.keys(typeCounts);
        const typeData = Object.values(typeCounts);

        // 2. Process data for Line Chart (Fatalities over time/Year-Month)
        // Sort rows by Date ascending for timeline
        const sortedRows = [...rows].sort((a, b) => new Date(a.date) - new Date(b.date));
        
        const timeFatalityMap = {};
        sortedRows.forEach(r => {
            if(!r.year) return;
            const period = r.month ? `${r.year}-${String(r.month).padStart(2, '0')}` : `${r.year}`;
            timeFatalityMap[period] = (timeFatalityMap[period] || 0) + (parseInt(r.fatalities) || 0);
        });

        const timeLabels = Object.keys(timeFatalityMap);
        const timeData = Object.values(timeFatalityMap);

        // --- Render Type Chart (Doughnut) ---
        if (typeChartInstance) typeChartInstance.destroy();
        const ctxType = document.getElementById('typeChart').getContext('2d');
        typeChartInstance = new Chart(ctxType, {
            type: 'doughnut',
            data: {
                labels: typeLabels,
                datasets: [{
                    data: typeData,
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(139, 92, 246, 0.8)'
                    ],
                    borderColor: 'rgba(0,0,0,0.2)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { boxWidth: 12, font: { size: 10 } }
                    }
                }
            }
        });

        // --- Render Time Chart (Line) ---
        if (timeChartInstance) timeChartInstance.destroy();
        const ctxTime = document.getElementById('timeChart').getContext('2d');
        timeChartInstance = new Chart(ctxTime, {
            type: 'line',
            data: {
                labels: timeLabels,
                datasets: [{
                    label: 'Fatalities',
                    data: timeData,
                    borderColor: 'rgba(239, 68, 68, 1)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: 'rgba(239, 68, 68, 1)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { maxRotation: 45, minRotation: 45, font: {size: 10} }
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

    // Search input debounce
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            fetchIncidents(e.target.value.trim());
        }, 300);
    });
});
