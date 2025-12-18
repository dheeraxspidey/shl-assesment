---
title: SHL Assessment Recommender
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# SHL Assessment Recommender

## Overview
This project implements a RAG-based recommendation system for SHL assessments. It uses:
-   **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
-   **Vector Store**: FAISS
-   **Reranking**: Google Gemini 2.5 Flash (via LangChain)
-   **API**: FastAPI

## Setup
1.  **Install Dependencies**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
    *(Note: Dependencies include `sentence-transformers`, `faiss-cpu`, `fastapi`, `uvicorn`, `langchain`, `langchain-google-genai`, `python-dotenv`)*

2.  **Environment Variables**:
    Create a `.env` file in the root directory:
    ```
    GOOGLE_API_KEY=your_api_key_here
    ```

3.  **Ingest Data**:
    ```bash
    python shl_recommender/src/ingest.py
    ```

## Running the API
To start the server (runs on port 8001):
```bash
# From the project root
source venv/bin/activate
python shl_recommender/src/app.py
```

## Evaluation
To calculate Recall@10 on the training set:
```bash
python shl_recommender/src/metrics.py
```

## API Usage
**Endpoint**: `POST /recommend`
**Body**:
```json
{
  "query": "Looking for a Java developer with good communication skills"
}
```
**Example**:
```bash
curl -X POST http://localhost:8001/recommend \
     -H "Content-Type: application/json" \
     -d '{"query": "Java developer"}'
```