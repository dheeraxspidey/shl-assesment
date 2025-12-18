import pandas as pd
import requests

API_URL = "http://localhost:8001/recommend"
FILE_PATH = "/home/a-dheeraj/Desktop/work/assesment-shl/shl-assesment/Gen_AI Dataset.xlsx"

def debug_first_query():
    print("Loading Train-Set...")
    df = pd.read_excel(FILE_PATH, sheet_name='Train-Set')
    
    # Get first query
    first_query = df.iloc[0]['Query']
    ground_truth_urls = df[df['Query'] == first_query]['Assessment_url'].tolist()
    
    print(f"\nQuery: {first_query}")
    print(f"Ground Truth URLs ({len(ground_truth_urls)}):")
    for u in ground_truth_urls:
        print(f"  - '{u}'")
        
    # Call API
    print("\nCalling API...")
    try:
        response = requests.post(API_URL, json={"query": first_query})
        response.raise_for_status()
        preds = response.json()
        pred_urls = [p['url'] for p in preds]
        
        print(f"Predicted URLs ({len(pred_urls)}):")
        for u in pred_urls:
            print(f"  - '{u}'")
            
        # Check intersection
        gt_set = set(u.strip().rstrip('/') for u in ground_truth_urls)
        pred_set = set(u.strip().rstrip('/') for u in pred_urls)
        
        intersection = gt_set.intersection(pred_set)
        print(f"\nIntersection ({len(intersection)}):")
        for u in intersection:
            print(f"  - '{u}'")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_first_query()
