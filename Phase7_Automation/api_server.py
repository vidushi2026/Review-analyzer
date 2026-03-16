import os
import sys
import sqlite3
from typing import Optional
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn
from contextlib import asynccontextmanager

# Local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
BASE_DIR = os.path.join(SCRIPT_DIR, '..')
sys.path.insert(0, BASE_DIR)
import pipeline
from Phase7_Automation.email_service import send_latest_report_email

DB_PATH = os.path.join(BASE_DIR, 'Phase3_Storage', 'reviews_data.db')

def scheduled_job():
    print("Running scheduled daily review processing job...")
    pipeline.run_job()
    ok, msg = send_latest_report_email()
    print(f"Auto email send: ok={ok} msg={msg}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup Background Scheduler
    scheduler = BackgroundScheduler()
    # Schedule to run daily at 8:00 AM
    scheduler.add_job(scheduled_job, 'cron', hour=8, minute=0)
    scheduler.start()
    print("APScheduler started: Daily job configured for 8:00 AM")
    yield
    # Shutdown cleanly
    scheduler.shutdown()
    print("APScheduler shutdown")

app = FastAPI(title="Groww Review Analyzer API", version="1.0.0", lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "Groww Review Analyzer API is running.", "status": "online"}

@app.post("/trigger")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """
    Manually triggers the entire review extraction, clustering, and summarization pipeline.
    Runs in the background.
    """
    background_tasks.add_task(pipeline.run_job)
    return {"message": "Pipeline triggered successfully. Running in the background."}

@app.get("/reports")
def get_reports():
    """
    Fetch historical weekly summaries from the database.
    Returns a list of reports (generation_date, md_summary, draft_email_text).
    """
    if not os.path.exists(DB_PATH):
        return {"reports": []}
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT id, generation_date, md_summary, draft_email_text FROM weekly_reports ORDER BY id DESC LIMIT 50"
    )
    rows = c.fetchall()
    conn.close()
    reports = [
        {
            "id": r["id"],
            "generation_date": r["generation_date"],
            "md_summary": r["md_summary"],
            "draft_email_text": r["draft_email_text"] or "",
        }
        for r in rows
    ]
    return {"reports": reports}


class SendEmailRequest(BaseModel):
    to_email: Optional[str] = None


@app.post("/send-email")
def send_email_to_recipient(request: SendEmailRequest):
    """
    Send the latest weekly report email draft to the given recipient.
    Recipient email is provided by the user from the frontend.
    """
    ok, msg = send_latest_report_email(to_email=request.to_email, subject="Daily Groww Product Insight Pulse")
    return {"ok": ok, "message": msg}


if __name__ == "__main__":
    print("Starting FastAPI Server with Scheduler...")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
