
import pandas as pd
import re
import os

def extract_name_from_url(url):
    # Extract the last part of the URL as the name
    if pd.isna(url):
        return "Unknown"
    match = re.search(r'/view/([^/]+)/?$', url)
    if match:
        return match.group(1).replace('-', ' ').title()
    return url

def rate_recommendations():
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'submission.csv')
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return

    unique_queries = df['Query'].unique()
    
    print(f"Found {len(unique_queries)} unique queries in {file_path}\n")
    
    for i, query in enumerate(unique_queries):
        print(f"Query {i+1}: {query[:100]}..." if len(query) > 100 else f"Query {i+1}: {query}")
        
        recs = df[df['Query'] == query]['Assessment_url'].tolist()
        print(f"  Recommendations ({len(recs)}):")
        
        for j, url in enumerate(recs):
            name = extract_name_from_url(url)
            print(f"    {j+1}. {name}")
        print("-" * 80)

if __name__ == "__main__":
    rate_recommendations()
