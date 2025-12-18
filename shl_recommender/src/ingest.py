import json
import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_FILE = os.path.join(DATA_DIR, "raw_assessments.json")
INDEX_FILE = os.path.join(DATA_DIR, "assessments.index")
METADATA_FILE = os.path.join(DATA_DIR, "assessments.pkl")

def ingest_data():
    print(f"Loading data from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r') as f:
        assessments = json.load(f)
    
    print(f"Found {len(assessments)} assessments.")
    
    # Prepare text for embedding
    texts = []
    for item in assessments:
        # Construct a rich representation
        # We include key fields that a user might query against
        text = (
            f"Title: {item.get('name', '')}\n"
            f"Description: {item.get('description', '')}\n"
            f"Test Type: {', '.join(item.get('test_type', []))}\n"
            f"Job Levels: {', '.join(item.get('job_levels', []))}\n"
            f"Languages: {', '.join(item.get('languages', []))}"
        )
        texts.append(text)
        
    print("Loading SentenceTransformer model (all-mpnet-base-v2)...")
    model = SentenceTransformer('all-mpnet-base-v2')
    
    print("Generating embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    
    # Create FAISS index
    print("Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save Index
    print(f"Saving index to {INDEX_FILE}...")
    faiss.write_index(index, INDEX_FILE)
    
    # Save Metadata (to map ID -> Assessment)
    print(f"Saving metadata to {METADATA_FILE}...")
    with open(METADATA_FILE, 'wb') as f:
        pickle.dump(assessments, f)
        
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_data()
