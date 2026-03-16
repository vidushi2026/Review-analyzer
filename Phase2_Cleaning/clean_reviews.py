import os
import json
import re
import emoji
from langdetect import detect, DetectorFactory
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Ensure consistent language detection
DetectorFactory.seed = 0

def contains_emoji(text):
    """Check if the text contains any emojis."""
    return emoji.emoji_count(text) > 0

def clean_reviews(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        reviews = json.load(f)

    # Setup Presidio for PII scrubbing
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    
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
            
        # 5. PII Scrubbing
        # We look for common PII: EMAIL_ADDRESS, PHONE_NUMBER, PERSON, etc.
        # Analyzing the text
        results = analyzer.analyze(text=text, entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON"], language='en')
        
        # Anonymizing
        anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
        scrubbed_text = anonymized_result.text
        
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
