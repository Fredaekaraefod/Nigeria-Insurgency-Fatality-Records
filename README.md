# Offline Conflict Registry | Boko Haram Incidents (2009 - 2026)

Welcome to the **Boko Haram Conflict Registry**. This is a fast, offline, and fully local database explorer that allows researchers and journalists to query over a decade of conflict data instantly.

## Features
- **Live Search & Filtering:** Use simple keywords (like "Bombing", "Borno", or "2015") to instantly filter and match records directly from the database schema.
- **Data Visualization Setup:** Dynamic visual representations (bars/charts) adapt to your current filters on the fly.
- **Zero API Dependency:** Completely stripped of LLM agent endpoints, running exactly as an offline, read-only SQLite wrapper optimized for safety and raw speed.

---

## Data Sources
This project's monolithic database (`incidents.db`) spans 831 isolated, strictly-verified conflict events seamlessly aggregated from multiple prestigious tracking registries:
- **Nigeria Security Tracker (NST):** The Council on Foreign Relations' highly structured dataset.
- **Wikipedia Timelines:** Fully scraped, parsed, and verified monthly incident timelines spanning from 2009 to 2026.
- **Amnesty International & Media Reports:** Secondary human-rights data independently isolated from detailed textual summaries.
*(All markdown data was rigorously deduplicated and verified before being injected into the unified SQLite query engine.)*

---

## Competition Setup & Vercel Deployment

This project is meticulously engineered to deploy seamlessly to **Vercel** serverless environments for instant demonstration.

### Cloud Live Hosting (Vercel)
The backend (`backend/main.py`) operates as a Python Serverless Function mapped natively via `vercel.json` alongside the frontend visual dashboard. 

To deploy your own copy instantly to the cloud:
1. Connect this GitHub repository to your Vercel Account.
2. Click Deploy! Due to the headless and offline-first nature, it automatically uses the bundled `incidents.db` avoiding any external API keys entirely.

### Running Locally
1. Ensure Python `3.9+` is installed on your machine.
2. Run `pip install -r requirements.txt`.
3. Launch the local FastAPI server dynamically: 
   ```bash
   uvicorn backend.main:app --reload
   ```
4. Open `frontend/index.html` locally in any modern web browser to access the dashboard.
