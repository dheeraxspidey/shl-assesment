
import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shl_recommender', 'src'))

from engine import RecommendationEngine

def generate_submission():
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(base_dir, 'shl_recommender', 'data', 'test.csv')
    submission_file = os.path.join(base_dir, 'submission.csv')

    # Load test data
    print(f"Loading test data from {test_file}...")
    df_test = pd.read_csv(test_file)
    
    # Initialize engine
    engine = RecommendationEngine()
    
    submission_rows = []
    
    print("Starting inference...")
    for index, row in df_test.iterrows():
        query = row['Query']
        print(f"Processing Query {index + 1}/{len(df_test)}: {query[:50]}...")
        
        try:
            recommendations = engine.recommend(query, top_n=10)
            
            # Ensure we have at least 5 recommendations as per requirement (min 5, max 10)
            # The engine returns up to top_n, so we should be good if there are enough candidates.
            
            for rec in recommendations:
                submission_rows.append({
                    'Query': query,
                    'Assessment_url': rec.get('url', '')
                })
                
        except Exception as e:
            print(f"Error processing query {index + 1}: {e}")
            # In case of error, maybe add empty rows or handle gracefully? 
            # For now, let's just print error.
            
    # Create submission DataFrame
    df_submission = pd.DataFrame(submission_rows)
    
    # Save to CSV
    print(f"Saving submission to {submission_file}...")
    df_submission.to_csv(submission_file, index=False)
    print("Done!")

if __name__ == "__main__":
    generate_submission()
