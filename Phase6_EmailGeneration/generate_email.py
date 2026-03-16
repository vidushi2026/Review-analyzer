import os
import sqlite3
import smtplib
from email.message import EmailMessage
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'Phase3_Storage', 'reviews_data.db')

def get_latest_report():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT id, md_summary FROM weekly_reports ORDER BY id DESC LIMIT 1')
    report = c.fetchone()
    conn.close()
    return report

def draft_email_with_llm(markdown_summary):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not found.")
        return None
        
    client = Groq(api_key=api_key)
    
    system_prompt = """You are a professional Product Operations Manager.
Your job is to take the provided weekly product insight pulse markdown and draft a formal, concise, and clean email to the Product Team.
The email should include a professional greeting, the summarized insights in a very readable format, and a polite sign-off.

Very important formatting rules:
- Convert any markdown headings or bullets into clean plain text sentences or numbered lists.
- Do NOT include markdown markers like '*', '-', '#', '```', or '**' anywhere in the email body.
- Headings such as **External Fund Tracking Issues** must appear as plain text like: External Fund Tracking Issues:

The sign-off MUST always end with:

Best regards,
Vidushi

Do not add any other name in the sign-off and do not change this wording.
Output ONLY the email body. Do not include subject lines or extra chatty text."""

    print("Calling Groq API to format email draft...")
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the markdown summary. Please draft the email body:\n\n{markdown_summary}"}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=800,
    )
    
    return chat_completion.choices[0].message.content

def save_email_draft_to_db(report_id, email_text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE weekly_reports
        SET draft_email_text = ?
        WHERE id = ?
    ''', (email_text, report_id))
    conn.commit()
    conn.close()

def send_email(subject, body, to_email):
    # This requires SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, and SENDER_PASSWORD in .env
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        print("\nEmail dispatch skipped.")
        print("To actually send emails, add SENDER_EMAIL and SENDER_PASSWORD (App Password) to your .env file.")
        return False
        
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email
    
    try:
        print(f"Sending email to {to_email} via {smtp_server}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def main():
    report = get_latest_report()
    if not report:
        print("No reports found in the database. Please run Phase 5 first.")
        return
        
    report_id = report['id']
    md_summary = report['md_summary']
    
    email_draft = draft_email_with_llm(md_summary)
    
    if email_draft:
        print("\n" + "="*50)
        print("GENERATED EMAIL DRAFT")
        print("="*50 + "\n")
        print(email_draft)
        print("\n" + "="*50 + "\n")
        
        save_email_draft_to_db(report_id, email_draft)
        print("Saved email draft back to the database.")
        print("Recipient is taken from the dashboard when you click 'Send email'.")

if __name__ == '__main__':
    main()
