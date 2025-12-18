import pandas as pd
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shl_recommender', 'src'))

from engine import RecommendationEngine

def normalize_url(url):
    if not isinstance(url, str):
        return ""
    return url.strip().replace('/solutions', '').rstrip('/')

def analyze():
    print("Loading data...")
    train_path = 'shl_recommender/data/train.csv'
    df = pd.read_csv(train_path)
    
    # Group ground truth by Query
    gt_grouped = df.groupby('Query')['Assessment_url'].apply(list).to_dict()
    
    print("Initializing Engine...")
    engine = RecommendationEngine()
    
    print(f"\nAnalyzing {len(gt_grouped)} queries (k=30)...")
    
    total_recall = 0
    count = 0
    
    for i, (query, gt_urls) in enumerate(gt_grouped.items()):
        # Get retrieved candidates (before reranking)
        candidates = engine.search(query, k=100)
        retrieved_urls = [c['url'] for c in candidates]
        
        # Normalize
        gt_set = set(normalize_url(u) for u in gt_urls)
        pred_set = set(normalize_url(u) for u in retrieved_urls)
        
        if len(gt_set) == 0:
            continue
            
        # Calculate Missing
        missing = gt_set - pred_set
        matches = len(gt_set.intersection(pred_set))
        recall = matches / len(gt_set)
        
        total_recall += recall
        count += 1
        
        if len(missing) > 0:
            print(f"\nQuery {i+1}: {query[:100]}...")
            print(f"  Recall: {recall:.2f} ({matches}/{len(gt_set)})")
            print(f"  Missing ({len(missing)}):")
            for m in missing:
                # Try to find the original URL for better readability if possible, or just print normalized
                print(f"    - {m}")
                
    print(f"\n--- Summary ---")
    print(f"Mean Retrieval Recall@30: {total_recall/count:.4f}")

if __name__ == "__main__":
    analyze()
