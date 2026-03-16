import os
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'Phase3_Storage', 'reviews_data.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def main():
    print("Loading SQLite database...")
    conn = get_db_connection()
    c = conn.cursor()
    
    # Fetch processed reviews
    c.execute('SELECT id, cleaned_text FROM processed_reviews WHERE cleaned_text IS NOT NULL AND cleaned_text != ""')
    reviews = c.fetchall()
    
    if not reviews:
        print("No processed reviews found to cluster.")
        return
        
    print(f"Loaded {len(reviews)} reviews for clustering.")
    
    texts = [row['cleaned_text'] for row in reviews]
    ids = [row['id'] for row in reviews]
    
    print("Loading SentenceTransformer model (all-MiniLM-L6-v2) ...")
    # This is a lightweight model perfect for clustering reviews
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Generating embeddings... This might take a minute.")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # Number of clusters
    k = min(5, len(texts))
    
    print(f"Applying K-Means clustering with k={k}...")
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(embeddings)
    
    cluster_labels = kmeans.labels_
    
    print("Updating database with cluster IDs...")
    for review_id, cluster_id in zip(ids, cluster_labels):
        c.execute('''
            UPDATE processed_reviews
            SET cluster_id = ?
            WHERE id = ?
        ''', (int(cluster_id), review_id))
    
    conn.commit()
    conn.close()
    
    print("Clustering completed successfully!")

if __name__ == "__main__":
    main()
