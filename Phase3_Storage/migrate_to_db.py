import os
import json
try:
    from .database import init_db, insert_raw_reviews, insert_processed_reviews
except ImportError:
    from database import init_db, insert_raw_reviews, insert_processed_reviews

def migrate():
    # Make sure DB is initialized
    init_db()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load Raw Reviews
    raw_path = os.path.join(script_dir, '..', 'Phase1_Ingestion', 'data', 'raw_reviews.json')
    if os.path.exists(raw_path):
        with open(raw_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        added = insert_raw_reviews(raw_data)
        print(f"Inserted {added} raw reviews into the database.")
    else:
        print("Raw reviews JSON not found.")
        
    # Load Processed Reviews
    cleaned_path = os.path.join(script_dir, '..', 'Phase2_Cleaning', 'data', 'cleaned_reviews.json')
    if os.path.exists(cleaned_path):
        with open(cleaned_path, 'r', encoding='utf-8') as f:
            cleaned_data = json.load(f)
        added = insert_processed_reviews(cleaned_data)
        print(f"Inserted {added} processed reviews into the database.")
    else:
        print("Cleaned reviews JSON not found.")

if __name__ == '__main__':
    migrate()
