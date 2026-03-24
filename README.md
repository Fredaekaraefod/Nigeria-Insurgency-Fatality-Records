# Natural Language Investigator | Boko Haram Conflict Registry (2009 - 2026)

Welcome to the **Natural Language Investigator**, an AI-powered analytical dashboard that allows researchers, journalists, and competition judges to query over a decade of Boko Haram conflict data using plain English.

## Features
- **Conversational Interface:** Ask complex spatial and temporal questions like *"List all ambush attacks reported by Amnesty International"* and instantly receive accurate, verifiable facts.
- **Agentic AI Architecture:** Powered entirely by **Meta's LLaMA-3.3 70B** model (running via Groq API) utilizing a resilient **Zero-Shot ReAct** architecture. The AI physically authors, executes, and parses SQL database queries in real-time, functioning completely autonomously as an intelligent database querying agent.
- **Thought Stream UI:** An exclusive, dark-mode terminal layout built purely on raw HTML/CSS/JS that streams the LLM's internal JSON actions, SQL formations, and observations so you can track *exactly* how the AI arrived at its conclusion in real-time.

---

## Data Sources
This project's monolithic database (`incidents.db`) spans 831 isolated, strictly-verified conflict events seamlessly aggregated from multiple prestigious tracking registries over the past two days:
- **Nigeria Security Tracker (NST):** The Council on Foreign Relations' highly structured dataset (`NST-Main Sheet.xlsx`).
- **Wikipedia Timelines:** Fully scraped, parsed, and verified monthly incident timelines spanning from 2009 to 2026.
- **Amnesty International & Media Reports:** Secondary human-rights data independently isolated from detailed textual summaries.
- *(All markdown data was rigorously deduplicated and verified before being injected into the unified SQLite query engine.)*

---

## Competition Setup & Vercel Deployment

This project is meticulously engineered to deploy seamlessly to **Vercel** serverless environments for instant demonstration.

### Cloud Live Hosting (Vercel)
The backend (`backend/main.py`) operates as a Python Serverless Function mapped natively via `vercel.json` alongside the frontend visual dashboard. 

To deploy your own copy instantly to the cloud:
1. Connect this GitHub repository to your Vercel Account.
2. In the Vercel Dashboard, navigate to **Settings > Environment Variables**.
3. Add a Variable named **`GROQ_API_KEY`** and securely paste your free API key from [console.groq.com](https://console.groq.com/keys).
4. Click Deploy. The frontend UI will automatically fetch results directly from your live serverless agent.

### Running Locally (For Judges or Developers)
1. Ensure Python is installed on your machine.
2. Run `pip install -r requirements.txt`.
3. Set your environment key: 
   - Windows: `set GROQ_API_KEY=your_key_here`
   - Mac/Linux: `export GROQ_API_KEY=your_key_here`
4. Launch the local FastAPI server dynamically: 
   ```bash
   uvicorn backend.main:app --reload
   ```
5. Open `frontend/index.html` locally in any modern web browser to access the dashboard.
