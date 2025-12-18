import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from engine import RecommendationEngine

app = FastAPI(title="SHL Assessment Recommender")

# Initialize Engine
engine = RecommendationEngine()

class RecommendRequest(BaseModel):
    query: Optional[str] = None
    url: Optional[str] = None

def scrape_url(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Simple extraction: get all text
        text = soup.get_text(separator=' ', strip=True)
        return text[:5000] # Limit to first 5000 chars to avoid token limits
    except Exception as e:
        print(f"Failed to scrape URL {url}: {e}")
        return ""

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/recommend")
def recommend(request: RecommendRequest):
    query_text = request.query
    
    if request.url:
        scraped_text = scrape_url(request.url)
        if scraped_text:
            if query_text:
                query_text += f"\n\nContext from URL:\n{scraped_text}"
            else:
                query_text = scraped_text
                
    if not query_text:
        raise HTTPException(status_code=400, detail="Please provide either a query or a valid URL.")
        
    # New Pipeline: Query Expansion -> Hybrid Search (BM25+FAISS) -> Full-Data LLM Rerank
    final_results = engine.recommend(query_text, top_n=10)
    
    # Format response
    response = []
    for item in final_results:
        response.append({
            "name": item['name'],
            "url": item['url'],
            "test_type": item['test_type']
        })
        
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
