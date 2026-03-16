import os
import sqlite3
import datetime
from groq import Groq
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'Phase3_Storage', 'reviews_data.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_clustered_reviews():
    conn = get_db_connection()
    c = conn.cursor()
    # Fetch reviews that have been assigned a cluster
    c.execute('SELECT cluster_id, cleaned_text FROM processed_reviews WHERE cluster_id IS NOT NULL')
    rows = c.fetchall()
    conn.close()
    
    clusters = {}
    for r in rows:
        cid = r['cluster_id']
        if cid not in clusters:
            clusters[cid] = []
        clusters[cid].append(r['cleaned_text'])
    
    return clusters

def generate_summary(clusters):
    # Initialize Groq client
    # Assumes GROQ_API_KEY is in the environment variables
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not found.")
        print("Please set it by running: export GROQ_API_KEY='your_api_key'")
        return None
        
    client = Groq(api_key=api_key)
    
    # Format the input for the prompt
    cluster_texts = []
    for cid, texts in clusters.items():
        # Let's send up to 20 representative reviews per cluster to save tokens while providing good context
        sample_size = min(20, len(texts)) 
        sample_texts = texts[:sample_size]
        cluster_texts.append(f"Cluster {cid} (Size: {len(texts)} total reviews):\n" + "\n".join([f"- {t}" for t in sample_texts]))
    
    prompt_input = "\n\n".join(cluster_texts)
    
    system_prompt = """You are an expert Product Manager analyzing app reviews for the app 'Groww'.
Your goal is to convert the clustered user reviews into a concise one-page markdown summary.
The summary MUST strictly contain:
1. Top 3 themes (derived from the most significant pain points or feature requests across the clusters).
2. 3 representative user quotes (verbatim quotes selected from the provided cleaned text).
3. 3 actionable product ideas based on the feedback.

Format your output in clean Markdown. Do NOT include any PII or sensitive data. Be concise and professional.
"""
    
    print("Calling Groq API (llama-3.3-70b-versatile) to generate summary...")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"Here are the recent app reviews grouped by thematic clusters. Please generate the one-page product insight pulse:\n\n{prompt_input}",
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        max_tokens=1024,
    )
    
    return chat_completion.choices[0].message.content

def save_report(markdown_summary):
    conn = get_db_connection()
    c = conn.cursor()
    
    generation_date = datetime.datetime.now().isoformat()
    
    c.execute('''
        INSERT INTO weekly_reports (generation_date, md_summary)
        VALUES (?, ?)
    ''', (generation_date, markdown_summary))
    
    conn.commit()
    report_id = c.lastrowid
    conn.close()
    
    return report_id

def main():
    print("Fetching clustered reviews from the database...")
    clusters = get_clustered_reviews()
    if not clusters:
        print("No clustered reviews found. Please run Phase 4 first.")
        return
        
    summary = generate_summary(clusters)
    if summary:
        print("\n" + "="*50)
        print("GENERATED SUMMARY")
        print("="*50 + "\n")
        print(summary)
        print("\n" + "="*50 + "\n")
        
        report_id = save_report(summary)
        print(f"Summary successfully saved to the database (Report ID: {report_id}).")
        
        # Save a local markdown file just for easy visibility
        report_file = os.path.join(SCRIPT_DIR, 'latest_weekly_report.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"Saved local copy to: {report_file}")

if __name__ == '__main__':
    main()
