from shl_recommender.src.metrics import calculate_recall_at_k
import pandas as pd

def demo_metric():
    print("--- Metric Calculation Demo ---\n")
    
    # Scenario: Ground Truth has 5 relevant items
    # We retrieve 10 items.
    
    # Case 1: We match 1 item out of 5
    print("Case 1: 1 Match out of 5 Relevant Items")
    gt_df = pd.DataFrame({
        'Query': ['Q1', 'Q1', 'Q1', 'Q1', 'Q1'],
        'Assessment_url': ['A', 'B', 'C', 'D', 'E']
    })
    pred_df = pd.DataFrame({
        'Query': ['Q1'],
        'Assessment_url': ['A'] # Only A is found
    })
    
    score = calculate_recall_at_k(pred_df, gt_df, k=10)
    print(f"Result: {score} (Expected: 1/5 = 0.2)\n")
    
    # Case 2: We match 3 items out of 5
    print("Case 2: 3 Matches out of 5 Relevant Items")
    pred_df_2 = pd.DataFrame({
        'Query': ['Q1', 'Q1', 'Q1'],
        'Assessment_url': ['A', 'B', 'C'] # A, B, C are found
    })
    score_2 = calculate_recall_at_k(pred_df_2, gt_df, k=10)
    print(f"Result: {score_2} (Expected: 3/5 = 0.6)\n")

if __name__ == "__main__":
    demo_metric()
