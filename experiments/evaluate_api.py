import pandas as pd
import requests
import time
import json

API_URL = "http://localhost:8001/recommend"
FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Gen_AI Dataset.xlsx")
OUTPUT_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "submission.csv")

def get_recommendations(query, url=None):
    payload = {"query": query}
    if url:
        payload["url"] = url
        
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling API: {e}")
        return []

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "shl_recommender", "src"))
from metrics import calculate_recall_at_k

def evaluate_recall():
    print("Loading Train-Set...")
    gt_df = pd.read_excel(FILE_PATH, sheet_name='Train-Set')
    
    # Generate Predictions for Train Set
    print("Generating predictions for Train Set...")
    queries = gt_df['Query'].unique()
    
    pred_data = []
    for query in queries:
        preds = get_recommendations(query)
        for p in preds:
            pred_data.append({
                "Query": query,
                "Assessment_url": p['url']
            })
            
    pred_df = pd.DataFrame(pred_data)
    
    # Calculate Metrics
    calculate_recall_at_k(pred_df, gt_df, k=10)


def generate_predictions():
    print("\nGenerating predictions for Test-Set...")
    df = pd.read_excel(FILE_PATH, sheet_name='Test-Set')
    
    results = []
    
    for idx, row in df.iterrows():
        query = row['Query']
        print(f"Processing Test Query {idx+1}/{len(df)}...")
        
        preds = get_recommendations(query)
        
        # Format for submission: Query, Assessment_url
        # We need to list recommendations for each query
        # The format example in assignment says:
        # Query 1 Recommendation 1
        # Query 1 Recommendation 2
        
        for p in preds:
            results.append({
                "Query": query,
                "Assessment_url": p['url']
            })
            
    # Save to CSV
    res_df = pd.DataFrame(results)
    res_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Predictions saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    # Ensure API is running
    try:
        requests.get("http://localhost:8001/health")
    except:
        print("API is not running! Please start src/app.py first.")
        exit(1)
        
    evaluate_recall()
    generate_predictions()
