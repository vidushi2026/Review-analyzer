import os
import json
import datetime
from google_play_scraper import Sort, reviews

APP_ID = 'com.nextbillion.groww'
MAX_REVIEWS = 500
WEEKS_LIMIT = 12

def fetch_groww_reviews():
    """
    Fetches reviews for Groww from the Google Play Store.
    Limits to the last 8-12 weeks and caps at MAX_REVIEWS (500).
    Extracts: reviewId, rating, review_text, date.
    """
    print(f"Fetching reviews for {APP_ID}...")
    
    # We fetch an initial batch larger than 500 since we'll filter by date,
    # but the final payload limit is 500. Let's fetch 2000 to be safe.
    result, _ = reviews(
        APP_ID,
        lang='en',
        country='in',
        sort=Sort.NEWEST,
        count=2000
    )
    
    cutoff_date = datetime.datetime.now() - datetime.timedelta(weeks=WEEKS_LIMIT)
    
    extracted_reviews = []
    
    for r in result:
        review_date = r.get('at')
        if review_date and review_date >= cutoff_date:
            content = r.get('content', '')
            
            # Filter out reviews with less than 5 words
            if not content or len(content.split()) < 5:
                continue
            
            extracted_reviews.append({
                'reviewId': r.get('reviewId'),
                'rating': r.get('score'),
                'review_text': content,
                'date': review_date.isoformat()
            })
            
        if len(extracted_reviews) >= MAX_REVIEWS:
            break
            
    return extracted_reviews

if __name__ == '__main__':
    fetched = fetch_groww_reviews()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, 'raw_reviews.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fetched, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully fetched {len(fetched)} reviews from the last {WEEKS_LIMIT} weeks.")
    print(f"Saved to {output_path}")
