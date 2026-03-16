# Phase-Wise Architecture: Groww Review Analyzer

## Objective
Convert recent Google Play Store reviews into a weekly one-page product insight pulse and automatically draft an email containing this summary.
- **LLM**: Groq
- **App**: Groww (Google Play Store)
- **Review Limit**: 500

---

## 1. Data Ingestion
- **Source**: Google Play Store scraper (e.g., `google-play-scraper` in Python).
- **Extraction**: Fetch reviews from the last 8–12 weeks. Extract only required fields: `reviewId`, `rating`, `review_text`, and `date`.
- **Limiting**: Limit the fetched reviews payload to a maximum of 500 reviews to comply with constraints and LLM context window limits.

## 2. Data Cleaning & Processing (Pre-LLM)
- **Spam/Duplicate Removal**: Filter out reviews with less than 5 words, exact text/date duplicates, non-English reviews, and any reviews containing emojis.
- **PII Scrubbing**: Apply rule-based regex (emails, phone numbers) and lightweight NLP (e.g., Microsoft `presidio` analyzer) to detect and redact Personably Identifiable Information (PII) to ensure strict privacy constraint compliance.

## 3. Storage
- **Database Choice**: SQLite implementation for simplicity and local execution.
- **Schema/Collections**:
   - `raw_reviews` (id, review_id, rating, review_text, date, ingested_at)
   - `processed_reviews` (id, raw_id, cleaned_text, cluster_id)
   - `weekly_reports` (id, generation_date, md_summary, draft_email_text)

## 4. Clustering & Thematic Grouping
- **Method**: Local Semantic Clustering.
- **Implementation**: 
  - Use an open-source lightweight embedding model (e.g., `sentence-transformers/all-MiniLM-L6-v2`) to generate embeddings for the 500 cleaned reviews.
  - Apply K-Means clustering (forced to `k=5`) or HDBSCAN (capped to top 5 clusters) to group the reviews into exactly 5 maximum themes, ensuring clear analytical boundaries before passing to the LLM.

## 5. LLM Summarization (Groq)
- **Model Choice**: Use a fast inference model via Groq API (e.g., Meta Llama-3-70B or Mixtral 8x7b).
- **Input Context**: Pass the 5 clustered review groups.
- **Prompt Instructions**: Request a strict, concise one-page markdown summary output containing:
  1. *Top 3 themes* (derived from the largest/most severe clusters).
  2. *3 representative user quotes* (verbatim quotes selected from the provided cleaned text, tied directly to the themes).
  3. *3 product action ideas* (inferred actions based on the user pain points/feature requests).

## 6. Email Generation
- **Drafting Process**: Chain a secondary LLM call to Groq, passing the generated one-page markdown summary to format it into a professional weekly memo email draft.
- **Sending/Forwarding**: Connect to an email service via API (e.g., SendGrid, Mailgun) or an SMTP library (`smtplib`), setting the drafted note as the `body`. Send the email payload to the specified product team email/alias.

## 7. Scheduler & Automation Pipeline
- **Orchestration**: GitHub Actions (Cron Workflow) or a lightweight orchestrator like APScheduler/Prefect.
- **Frequency**: Run weekly (e.g., every Monday at 8:00 AM).
- **Execution Flow**: 
  1. Trigger Ingestion Script
  2. Execute Cleaning & NLP Clustering
  3. Call Groq for Summary & Email Draft
  4. Fire Email API dispatcher
  5. Save Run status and outputs to Database

## 8. Frontend & Backend
- **Backend API**: A lightweight FastAPI wrapper. Exposes a `/trigger` endpoint to run the job manually, and a `/reports` endpoint to fetch historical weekly summaries.
- **Frontend Dashboard**: A simple Streamlit interface for product managers to:
  - View historical one-page weekly summaries.
  - Approve or edit the drafted email before finalizing and sending (Human-in-the-loop).
  - Add or update the list of designated email recipients or aliases.
