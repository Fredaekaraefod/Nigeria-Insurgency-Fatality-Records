document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('queryInput');
    const submitBtn = document.getElementById('submitBtn');
    const thoughtStream = document.getElementById('thoughtStream');
    const resultContent = document.getElementById('resultContent');
    const spinner = document.getElementById('agentSpinner');

    async function sendQuery() {
        const query = input.value.trim();
        if (!query) return;

        // Reset UI
        thoughtStream.innerHTML = '';
        resultContent.innerHTML = '';
        spinner.style.display = 'block';
        submitBtn.disabled = true;
        
        appendLog(`[SYSTEM] Initializing Agent...\n[USER] ${query}`, 'system');

        try {
            // Pointing directly to the Vercel API Serverless route
            const response = await fetch('/api/investigate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            const data = await response.json();

            if (data.success) {
                // Render Agent Thoughts sequentially to simulate streaming
                let delay = 0;
                
                data.thought_process.forEach((step, index) => {
                    setTimeout(() => {
                        appendLog(`[ACTION] ${step.action}`, 'action');
                        if (step.input) {
                            appendLog(`[INPUT] ${step.input}`, 'query');
                        }
                        appendLog(`[OBSERVATION] ${step.observation}`, 'observation');
                    }, delay);
                    delay += 600; // Simulated typing / thinking block delay
                });

                // Render Final Output after thoughts finish typing
                setTimeout(() => {
                    renderFinalResult(data.final_answer, data.sql_query);
                    spinner.style.display = 'none';
                    submitBtn.disabled = false;
                    appendLog('[SYSTEM] Execution Complete.', 'system');
                }, delay + 500);

            } else {
                appendLog(`[ERROR] ${data.error}`, 'observation');
                spinner.style.display = 'none';
                submitBtn.disabled = false;
            }

        } catch (err) {
            appendLog(`[SYSTEM FATAL ERROR] Backend not reachable. Ensure FastAPI server is running on localhost:8000.`, 'observation');
            spinner.style.display = 'none';
            submitBtn.disabled = false;
        }
    }

    function appendLog(text, type) {
        const div = document.createElement('div');
        div.className = `log-entry ${type}`;
        div.textContent = text;
        thoughtStream.appendChild(div);
        thoughtStream.scrollTop = thoughtStream.scrollHeight;
    }

    function renderFinalResult(answer, sql) {
        let html = `<div class="final-answer">${answer}</div>`;
        
        if (sql && sql !== "No SQL query generated.") {
            html += `
                <div class="sql-badge"><i class="ph-fill ph-database"></i> Executed Query</div>
                <div class="sql-block">${sql}</div>
            `;
        }
        
        resultContent.innerHTML = html;
    }

    submitBtn.addEventListener('click', sendQuery);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendQuery();
    });
});
