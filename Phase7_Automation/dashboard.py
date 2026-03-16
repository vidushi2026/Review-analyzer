import os
import sqlite3
import streamlit as st
from dotenv import load_dotenv

# Load env variables (local .env)
load_dotenv()

def _get(key: str, default: str = "") -> str:
    """Use Streamlit Cloud secrets if available, else env."""
    try:
        v = st.secrets.get(key, default)
        return (v or default).strip()
    except Exception:
        return (os.environ.get(key, default) or default).strip()

# API base URL for send-email (Streamlit Cloud: set REVIEW_ANALYZER_API_URL in Secrets)
API_BASE = _get("REVIEW_ANALYZER_API_URL", "http://localhost:8000")
DEFAULT_RECIPIENT = _get("REPORT_RECIPIENT_EMAIL") or _get("TARGET_EMAIL") or _get("SENDER_EMAIL") or ""

st.set_page_config(page_title="Groww Review Analyzer", page_icon="📈", layout="wide")

st.title("📈 Groww Product Pulse Dashboard")
st.markdown("Convert recent Play Store reviews into weekly product insights.")

# Database Path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Phase3_Storage', 'reviews_data.db')

def fetch_latest_report():
    if not os.path.exists(DB_PATH):
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT md_summary, draft_email_text, generation_date FROM weekly_reports ORDER BY id DESC LIMIT 1')
        report = c.fetchone()
        conn.close()
        return dict(report) if report else None
    except:
        return None

def fetch_metrics():
    if not os.path.exists(DB_PATH):
        return {"raw": 0, "processed": 0}
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM raw_reviews')
        raw = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM processed_reviews')
        processed = c.fetchone()[0]
        conn.close()
        return {"raw": raw, "processed": processed}
    except:
        return {"raw": 0, "processed": 0}

metrics = fetch_metrics()

col1, col2, col3 = st.columns(3)
col1.metric("Raw Reviews Scraped", metrics['raw'])
col2.metric("Cleaned Active Reviews", metrics['processed'])
col3.metric("Last Run Status", "Success" if fetch_latest_report() else "Never Run")

st.divider()

report = fetch_latest_report()

if report:
    st.subheader(f"Latest Daily Report Generation: {report['generation_date']}")
    
    tab1, tab2 = st.tabs(["Markdown Summary", "Generated Email Draft"])
    
    with tab1:
        st.markdown(report['md_summary'])
        
    with tab2:
        st.text_area("Ready-to-Send Email Draft", report['draft_email_text'], height=400)

    st.divider()
    st.subheader("Send report by email")
    recipient_email = st.text_input(
        "Recipient email",
        value="",
        placeholder="e.g. you@company.com",
        help="Enter the email address to send the report to.",
    )
    if st.button("Send to Email"):
        if not recipient_email or "@" not in recipient_email:
            st.error("Please enter a valid recipient email address.")
        else:
            to_send = recipient_email.strip()
            sent = False
            # Try API first (when API server is running)
            try:
                import urllib.request
                import json
                req = urllib.request.Request(
                    f"{API_BASE}/send-email",
                    data=json.dumps({"to_email": to_send}).encode("utf-8"),
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode())
                if data.get("ok"):
                    st.success("Email sent successfully.")
                    sent = True
                else:
                    st.error(data.get("message", "Failed to send email."))
            except Exception as api_err:
                # Fallback: send directly from dashboard when API is not running
                try:
                    import sys
                    _script_dir = os.path.dirname(os.path.abspath(__file__))
                    _base = os.path.abspath(os.path.join(_script_dir, ".."))
                    if _base not in sys.path:
                        sys.path.insert(0, _base)
                    from Phase7_Automation.email_service import send_latest_report_email
                    ok, msg = send_latest_report_email(to_email=to_send, db_path=DB_PATH)
                    if ok:
                        st.success(msg)
                        sent = True
                    else:
                        st.error(msg)
                except Exception as direct_err:
                    st.error(
                        f"Could not send email. "
                        f"API at {API_BASE} is not running ({api_err}). "
                        f"Direct send failed: {direct_err}. "
                        "Ensure SENDER_EMAIL and SENDER_PASSWORD are set in .env."
                    )
    st.info("Automation: daily 8 AM generates the report and sends it to the default recipient.")
else:
    st.warning("No reports found in the database. Please run the data pipeline!")

st.divider()
st.subheader("Manual Pipeline Testing")
if st.button("🚀 Trigger Full Pipeline Extraction Core"):
    # This invokes the pipeline.py directly in the background
    with st.spinner("Running full pipeline (Ingest -> Clean -> Store -> Cluster -> Summarize -> Email)... this takes about 1-2 minutes."):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pipeline_path = os.path.join(script_dir, "pipeline.py")
        import subprocess
        import sys
        base_dir = os.path.join(script_dir, '..')
        subprocess.run([sys.executable, pipeline_path], cwd=os.path.abspath(base_dir))
        st.success("Pipeline executed successfully! Refreshing dashboard...")
        st.rerun()
