import json
import pandas as pd
import os

def normalize_url(url):
    if not isinstance(url, str):
        return ""
    return url.strip().replace('/solutions', '').rstrip('/')

def check_integrity():
    print("Loading raw_assessments.json...")
    with open('shl_recommender/data/raw_assessments.json', 'r') as f:
        raw_data = json.load(f)
    
    # Create a set of normalized URLs from raw data
    raw_urls = set()
    for item in raw_data:
        if 'url' in item:
            raw_urls.add(normalize_url(item['url']))
            
    print(f"Loaded {len(raw_urls)} unique assessments from raw data.")
    
    print("Loading train.csv...")
    df = pd.read_csv('shl_recommender/data/train.csv')
    
    # Get all unique ground truth URLs
    gt_urls = df['Assessment_url'].unique()
    print(f"Found {len(gt_urls)} unique ground truth assessments in train.csv.")
    
    missing_count = 0
    print("\n--- Missing Assessments ---")
    for url in gt_urls:
        norm_url = normalize_url(url)
        if norm_url not in raw_urls:
            print(f"MISSING: {url}")
            missing_count += 1
            
    if missing_count == 0:
        print("\nSUCCESS: All ground truth assessments are present in raw_assessments.json!")
    else:
        print(f"\nFAILURE: {missing_count} ground truth assessments are MISSING from raw_assessments.json.")
        print("These items cannot be retrieved because they are not in the index.")

if __name__ == "__main__":
    check_integrity()
