import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reviews_data.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Raw reviews table
    c.execute('''
        CREATE TABLE IF NOT EXISTS raw_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id TEXT UNIQUE,
            rating INTEGER,
            review_text TEXT,
            date TEXT,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Processed reviews table
    c.execute('''
        CREATE TABLE IF NOT EXISTS processed_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER,
            cleaned_text TEXT,
            cluster_id INTEGER,
            FOREIGN KEY(raw_id) REFERENCES raw_reviews(id)
        )
    ''')
    
    # Weekly reports table
    c.execute('''
        CREATE TABLE IF NOT EXISTS weekly_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generation_date TEXT,
            md_summary TEXT,
            draft_email_text TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def insert_raw_reviews(reviews_list):
    conn = get_db_connection()
    c = conn.cursor()
    count = 0
    for r in reviews_list:
        try:
            c.execute('''
                INSERT OR IGNORE INTO raw_reviews (review_id, rating, review_text, date)
                VALUES (?, ?, ?, ?)
            ''', (r.get('reviewId'), r.get('rating'), r.get('review_text'), r.get('date')))
            if c.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"Error inserting raw review {r.get('reviewId')}: {e}")
    conn.commit()
    conn.close()
    return count

def insert_processed_reviews(processed_list):
    conn = get_db_connection()
    c = conn.cursor()
    count = 0
    for r in processed_list:
        review_id = r.get('reviewId')
        c.execute('SELECT id FROM raw_reviews WHERE review_id = ?', (review_id,))
        row = c.fetchone()
        if row:
            raw_id = row['id']
            # Check if it's already there to avoid duplicates
            c.execute('SELECT id FROM processed_reviews WHERE raw_id = ?', (raw_id,))
            if not c.fetchone():
                c.execute('''
                    INSERT INTO processed_reviews (raw_id, cleaned_text)
                    VALUES (?, ?)
                ''', (raw_id, r.get('review_text')))
                count += 1
    conn.commit()
    conn.close()
    return count

if __name__ == '__main__':
    init_db()
