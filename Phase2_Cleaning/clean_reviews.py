import os
import json
import re
import emoji
from langdetect import detect, DetectorFactory

# Ensure consistent language detection
DetectorFactory.seed = 0


def contains_emoji(text):
    """Check if the text contains any emojis."""
    return emoji.emoji_count(text) > 0


def basic_pii_scrub(text: str) -> str:
    """
    Lightweight PII scrubbing using regex only.
    Removes common email addresses and phone-like patterns.
    """
    # Email addresses
    text = re.sub(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "[EMAIL]",
        text,
    )
    # Phone numbers (very simple heuristic: long digit sequences, with optional +, spaces, or dashes)
    text = re.sub(
        r"\+?\d[\d\s\-]{7,}\d",
        "[PHONE]",
        text,
    )
    return text


def clean_reviews(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        reviews = json.load(f)

    # Track seen texts to remove duplicates
    seen_texts = set()
    cleaned_reviews = []
    
    print(f"Loaded {len(reviews)} raw reviews.")
    
    for r in reviews:
        text = r.get('review_text', '')
        
        # 1. Emoji filter
        if contains_emoji(text):
            continue
            
        # 2. Duplicate filter (exact text)
        text_lower = text.strip().lower()
        if text_lower in seen_texts:
            continue
        seen_texts.add(text_lower)
        
        # 3. Word count filter (already in Phase 1, but good to ensure)
        if len(text.split()) < 5:
            continue
            
        # 4. English Language Filter
        try:
            if detect(text) != 'en':
                continue
        except:
            # If langdetect fails (e.g., text is all numbers or gibberish), we skip
            continue
            
        # 5. PII Scrubbing (regex-only, no external services)
        scrubbed_text = basic_pii_scrub(text)
        
        # Final cleaned review
        r['review_text'] = scrubbed_text
        cleaned_reviews.append(r)
        
    print(f"Retained {len(cleaned_reviews)} reviews after cleaning and PII scrubbing.")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_reviews, f, indent=2, ensure_ascii=False)
        
    print(f"Cleaned reviews saved to {output_path}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Input is from Phase 1
    input_file = os.path.abspath(os.path.join(script_dir, '..', 'Phase1_Ingestion', 'data', 'raw_reviews.json'))
    # Output is saved to Phase 2 data folder
    output_file = os.path.join(script_dir, 'data', 'cleaned_reviews.json')
    
    clean_reviews(input_file, output_file)
