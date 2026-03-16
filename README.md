# Groww Review Analyzer

Turns Google Play Store reviews into a daily product insight report and email draft.

## Run locally

1. **Create venv and install dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. **Configure `.env`** (copy from `.env.example` if present)
   - `GROQ_API_KEY` – required for summaries
   - `SENDER_EMAIL`, `SENDER_PASSWORD` – for sending report emails
   - `REPORT_RECIPIENT_EMAIL` – default recipient for automated/manual send

3. **Run the dashboard**
   ```bash
   streamlit run Phase7_Automation/dashboard.py
   ```
   Open **http://localhost:8501**

4. **Optional: run API + scheduler** (for `/trigger`, `/send-email`, daily 8 AM job)
   ```bash
   python Phase7_Automation/api_server.py
   ```
   API: http://localhost:8000

## Deploy on Streamlit Cloud

1. Push this repo to GitHub (e.g. [vidushi2026/Review-analyzer](https://github.com/vidushi2026/Review-analyzer)).

2. In [Streamlit Community Cloud](https://share.streamlit.io/), click **New app**:
   - **Repository**: `vidushi2026/Review-analyzer`
   - **Branch**: `main`
   - **Main file path**: `Phase7_Automation/dashboard.py`
   - **App URL**: choose a name (e.g. `review-analyzer`).

3. **Secrets** (in the app’s **Settings → Secrets**), add:
   ```toml
   REPORT_RECIPIENT_EMAIL = "your@email.com"
   REVIEW_ANALYZER_API_URL = "https://your-api-url.com"
   ```
   If the API is not deployed, leave `REVIEW_ANALYZER_API_URL` unset; the dashboard still works for viewing/triggering the pipeline; “Send to Email” will need the API.

4. Deploy. The app will be available at `https://<your-app-name>.streamlit.app`.

## Project layout

- `Phase1_Ingestion` – fetch Play Store reviews  
- `Phase2_Cleaning` – clean & PII scrub  
- `Phase3_Storage` – SQLite DB  
- `Phase4_Clustering` – thematic clustering  
- `Phase5_Summarization` – LLM summary  
- `Phase6_EmailGeneration` – email draft  
- `Phase7_Automation` – pipeline, API, scheduler, dashboard  
