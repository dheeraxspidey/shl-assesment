import pandas as pd
import numpy as np

def normalize_url(url):
    """
    Normalize URL for comparison:
    - Strip whitespace
    - Remove trailing slashes
    - Handle /solutions/products/ vs /products/ path inconsistency
    """
    if not isinstance(url, str):
        return ""
    url = url.strip().rstrip('/')
    # Handle /solutions/products/ -> /products/ conversion (ground truth uses this format)
    url = url.replace('/solutions/products/', '/products/')
    # Also handle any remaining /solutions/ paths
    url = url.replace('/solutions/', '/')
    return url

def calculate_recall_at_k(predictions_df, ground_truth_df, k=10, exclude_prepackaged=True):
    """
    Calculate Mean Recall@K.
    
    Args:
        predictions_df: DataFrame with columns ['Query', 'Assessment_url']
        ground_truth_df: DataFrame with columns ['Query', 'Assessment_url']
        k: Top-k items to consider
        exclude_prepackaged: If True, exclude Pre-packaged Job Solutions from GT
        
    Returns:
        float: Mean Recall@K
    """
    import json
    import os
    
    # Load scraped Individual Tests to identify pre-packaged URLs
    prepackaged_set = set()
    if exclude_prepackaged:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raw_path = os.path.join(base_dir, "data", "raw_assessments.json")
        if os.path.exists(raw_path):
            with open(raw_path, 'r') as f:
                assessments = json.load(f)
            scraped_urls = set(normalize_url(a['url']) for a in assessments)
            # URLs in GT but not in scraped = Pre-packaged
            for url in ground_truth_df['Assessment_url'].unique():
                if normalize_url(url) not in scraped_urls:
                    prepackaged_set.add(normalize_url(url))
            print(f"Excluding {len(prepackaged_set)} Pre-packaged URLs from Ground Truth:")
            for url in sorted(prepackaged_set):
                print(f"  - {url.split('/')[-1]}")
    
    # Group by Query
    gt_grouped = ground_truth_df.groupby('Query')['Assessment_url'].apply(list).to_dict()
    pred_grouped = predictions_df.groupby('Query')['Assessment_url'].apply(list).to_dict()
    
    total_recall = 0
    count = 0
    
    print(f"\n--- Calculating Recall@{k} (Individual Tests Only) ---")
    
    for query, gt_urls in gt_grouped.items():
        if query not in pred_grouped:
            print(f"Warning: No predictions for query: {query[:30]}...")
            continue
            
        # Get Top-K predictions
        pred_urls = pred_grouped[query][:k]
        
        # Normalize and filter out pre-packaged
        gt_normalized = [normalize_url(u) for u in gt_urls]
        gt_filtered = [u for u in gt_normalized if u not in prepackaged_set]
        
        if len(gt_filtered) == 0:
            continue
            
        gt_set = set(gt_filtered)
        pred_set = set(normalize_url(u) for u in pred_urls)
        
        # Calculate Intersection
        matches = len(gt_set.intersection(pred_set))
        recall = matches / len(gt_set)
        
        total_recall += recall
        count += 1
            
    mean_recall = total_recall / count if count > 0 else 0
    print(f"Processed {count} queries.")
    print(f"Mean Recall@{k}: {mean_recall:.4f}")
    return mean_recall

def calculate_diversity_score(predictions_df):
    """
    Calculate a heuristic 'Diversity Score' to measure balance.
    This requires 'Test Type' information which might not be in the CSV.
    If we only have URLs, we can't easily compute this without looking up metadata.
    
    For now, this is a placeholder or requires a lookup dictionary.
    """
    pass

import requests
import os

def get_api_predictions(queries, api_url="http://localhost:8002/recommend"):
    results = []
    print(f"Fetching predictions for {len(queries)} queries...")
    for i, q in enumerate(queries):
        print(f"  Query {i+1}/{len(queries)}...")
        try:
            resp = requests.post(api_url, json={"query": q})
            resp.raise_for_status()
            preds = resp.json()
            for p in preds:
                results.append({"Query": q, "Assessment_url": p['url']})
        except Exception as e:
            print(f"  Error: {e}")
    return pd.DataFrame(results)

if __name__ == "__main__":
    # Path to train.csv: ../data/train.csv relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    train_path = os.path.join(base_dir, "data", "train.csv")
    
    if not os.path.exists(train_path):
        print(f"Error: {train_path} not found.")
        exit(1)
        
    print(f"Loading Ground Truth from {train_path}...")
    gt_df = pd.read_csv(train_path)
    
    unique_queries = gt_df['Query'].unique()
    pred_df = get_api_predictions(unique_queries)

    output_path = os.path.join(base_dir, "data", "train_output.csv")
    print(f"Saving predictions to {output_path}...")
    pred_df.to_csv(output_path, index=False)
    
    calculate_recall_at_k(pred_df, gt_df, k=10)
