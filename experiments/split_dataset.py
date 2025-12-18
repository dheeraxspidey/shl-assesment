import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "shl_recommender", "data")
INPUT_FILE = os.path.join(BASE_DIR, "Gen_AI Dataset.xlsx")

def split_dataset():
    print(f"Reading {INPUT_FILE}...")
    xl = pd.ExcelFile(INPUT_FILE)
    
    # Train Set
    if 'Train-Set' in xl.sheet_names:
        print("Extracting Train-Set...")
        train_df = xl.parse('Train-Set')
        train_path = os.path.join(DATA_DIR, "train.csv")
        train_df.to_csv(train_path, index=False)
        print(f"Saved {len(train_df)} rows to {train_path}")
    else:
        print("Warning: 'Train-Set' sheet not found.")
        
    # Test Set
    if 'Test-Set' in xl.sheet_names:
        print("Extracting Test-Set...")
        test_df = xl.parse('Test-Set')
        test_path = os.path.join(DATA_DIR, "test.csv")
        test_df.to_csv(test_path, index=False)
        print(f"Saved {len(test_df)} rows to {test_path}")
    else:
        print("Warning: 'Test-Set' sheet not found.")

if __name__ == "__main__":
    # Ensure data dir exists
    os.makedirs(DATA_DIR, exist_ok=True)
    split_dataset()
