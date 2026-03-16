import os
import sqlite3
from typing import Optional, Tuple

from Phase6_EmailGeneration.generate_email import send_email as send_email_fn


def _get_db_path() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(script_dir, ".."))
    return os.path.join(base_dir, "Phase3_Storage", "reviews_data.db")


def get_default_recipient_email() -> str:
    """
    Default recipient for automated/manual "send to my email".
    Priority:
      1) REPORT_RECIPIENT_EMAIL
      2) TARGET_EMAIL (backward compatibility)
      3) SENDER_EMAIL
    """
    return (
        os.environ.get("REPORT_RECIPIENT_EMAIL")
        or os.environ.get("TARGET_EMAIL")
        or os.environ.get("SENDER_EMAIL")
        or ""
    ).strip()


def get_latest_draft_email_text(db_path: Optional[str] = None) -> Optional[str]:
    db_path = db_path or _get_db_path()
    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        """
        SELECT draft_email_text
        FROM weekly_reports
        WHERE draft_email_text IS NOT NULL AND draft_email_text != ''
        ORDER BY id DESC
        LIMIT 1
        """
    )
    row = c.fetchone()
    conn.close()
    return row["draft_email_text"] if row else None


def send_latest_report_email(
    to_email: Optional[str] = None,
    subject: str = "Daily Groww Product Insight Pulse",
    db_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Sends the *latest* saved email draft from the DB.
    Reuses Phase 6 SMTP sending logic and does not regenerate reports.
    """
    recipient = (to_email or get_default_recipient_email()).strip()
    if not recipient or "@" not in recipient:
        return False, "Valid recipient email is required."

    draft = get_latest_draft_email_text(db_path=db_path)
    if not draft:
        return False, "No email draft found. Run the pipeline to generate a report and draft."

    success = send_email_fn(subject, draft, recipient)
    if success:
        return True, "Email sent successfully."
    return False, "Failed to send email. Check SENDER_EMAIL and SENDER_PASSWORD in .env."

