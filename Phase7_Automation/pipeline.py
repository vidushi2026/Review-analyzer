import os
import sys

# Paths to the scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, '..')
sys.path.append(BASE_DIR)

from Phase1_Ingestion import ingest_reviews
from Phase2_Cleaning import clean_reviews
from Phase3_Storage import database, migrate_to_db
from Phase4_Clustering import cluster_reviews
from Phase5_Summarization import summarize
from Phase6_EmailGeneration import generate_email

def run_job():
    print("=======================================")
    print("STARTING GOOGLE PLAY REVIEW PIPELINE")
    print("=======================================")
    
    def run_script(rel_path):
        path = os.path.join(BASE_DIR, rel_path)
        # Quote paths so paths with spaces (e.g. "Review Analyzer") work in shell
        os.system(f'"{sys.executable}" "{path}"')

    # 1. Ingestion
    print("\n[Phase 1] Data Ingestion")
    run_script("Phase1_Ingestion/ingest_reviews.py")

    # 2. Cleaning
    print("\n[Phase 2] Data Cleaning & PII Scrubbing")
    run_script("Phase2_Cleaning/clean_reviews.py")

    # 3. Storage DB Migration
    print("\n[Phase 3] Database Migration")
    run_script("Phase3_Storage/migrate_to_db.py")

    # 4. Clustering
    print("\n[Phase 4] Thematic Clustering")
    run_script("Phase4_Clustering/cluster_reviews.py")

    # 5. Summarization
    print("\n[Phase 5] LLM Summarization")
    run_script("Phase5_Summarization/summarize.py")

    # 6. Email Draft & Send
    print("\n[Phase 6] Email Generation")
    run_script("Phase6_EmailGeneration/generate_email.py")
    
    print("\n=======================================")
    print("PIPELINE EXECUTION COMPLETE")
    print("=======================================")

if __name__ == "__main__":
    run_job()
