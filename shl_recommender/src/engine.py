import os
import json
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional, Dict, Any, List
from rank_bm25 import BM25Okapi
import re

# Load environment variables
load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_FILE = os.path.join(DATA_DIR, "assessments.index")
METADATA_FILE = os.path.join(DATA_DIR, "assessments.pkl")
RAW_DATA_FILE = os.path.join(DATA_DIR, "raw_assessments.json")

class RecommendationEngine:
    def __init__(self):
        print("Loading Recommendation Engine...")
        self.model = SentenceTransformer('all-mpnet-base-v2')
        
        # Check if indices exist, if not rebuild
        if not os.path.exists(INDEX_FILE) or not os.path.exists(METADATA_FILE):
            print("Indices not found. Rebuilding from raw data...")
            from ingest import ingest_data
            ingest_data()
            
        self.index = faiss.read_index(INDEX_FILE)
        with open(METADATA_FILE, 'rb') as f:
            self.metadata = pickle.load(f)
        
        # Build BM25 index for hybrid retrieval
        self._build_bm25_index()
            
        # Configure Gemini via LangChain
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemma-3-27b-it",
                google_api_key=api_key,
                temperature=0.1
            )
        else:
            print("WARNING: GOOGLE_API_KEY not found. LLM features will be disabled.")
            self.llm = None
    
    def _build_bm25_index(self):
        """Build BM25 index from assessment metadata for keyword matching."""
        print("Building BM25 index...")
        corpus = []
        for item in self.metadata:
            # Combine name, description, and test types for BM25
            text = f"{item['name']} {item.get('description', '')} {' '.join(item.get('test_type', []))}"
            # Tokenize
            tokens = re.findall(r'\w+', text.lower())
            corpus.append(tokens)
        self.bm25 = BM25Okapi(corpus)
        print(f"BM25 index built with {len(corpus)} documents.")

    def expand_query(self, query: str) -> str:
        """
        Use LLM to expand user query with awareness of available assessment types and skills.
        Includes catalog context for better vocabulary matching.
        """
        if not self.llm:
            return query

        # Catalog context - available assessment types and common skill keywords
        catalog_context = """
AVAILABLE ASSESSMENT TYPES:
- Ability & Aptitude (numerical, verbal, inductive reasoning)
- Knowledge & Skills (Java, Python, SQL, Excel, HTML/CSS, Selenium, etc.)
- Personality & Behavior (OPQ32r, leadership assessment)
- Simulations (Automata coding tests, SVAR spoken English)
- Competencies (interpersonal communications, business communication)
- Development & 360 (leadership reports, team assessment)

COMMON SKILL KEYWORDS IN OUR CATALOG:
Programming: Java, Python, SQL, JavaScript, C++, .NET, Selenium, HTML, CSS, PHP
Business: Sales, Marketing, Management, Customer Service, Administrative
Technical: Engineering, Data, Analytics, QA, Testing, Automation
Soft Skills: Communication, Leadership, Interpersonal, Collaboration
Levels: Entry Level, Advanced, Professional, Manager, Executive
"""

        template = """
        You are an expert at understanding job requirements and matching them to SHL assessment tests.
        
        {catalog_context}
        
        User Query: "{query}"
        
        Task: Expand this query to include SPECIFIC TOOLS and HARD SKILLS mentioned.
        The client prioritizes exact tool matches (e.g., Excel, Selenium, Java) over general role descriptions.
        
        Instructions:
        1. Identify every specific tool, language, or software mentioned (e.g., "Excel", "Python", "SEO").
        2. Map these to catalog keywords (e.g., "Microsoft Excel 365", "Search Engine Optimization").
        3. Include general role keywords only as secondary context.
        
        For example:
        - "Marketing Manager with Excel" → "Microsoft Excel 365, Excel, Data Analysis, Marketing, Digital Advertising"
        - "Java developer" → "Core Java, Java 8, Automata, programming, coding simulation"
        
        Return ONLY the expanded query (2-3 sentences max), heavily weighted towards specific hard skills.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({"query": query, "catalog_context": catalog_context})
            expanded = response.content.strip()
            print(f"Expanded Query: {expanded}")
            return expanded
        except Exception as e:
            print(f"Query expansion failed: {e}")
            return query

    def hybrid_search(self, query: str, k: int = 20) -> List[Dict]:
        """
        Hybrid retrieval using BM25 (keyword) + FAISS (semantic).
        Returns top-k candidates combining both methods.
        """
        # 1. Expand query for better retrieval
        expanded_query = self.expand_query(query)
        
        # 2. BM25 keyword search
        query_tokens = re.findall(r'\w+', expanded_query.lower())
        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_top_indices = np.argsort(bm25_scores)[::-1][:k]
        
        # 3. FAISS semantic search
        query_vector = self.model.encode([expanded_query]).astype('float32')
        distances, faiss_indices = self.index.search(query_vector, k)
        faiss_top_indices = faiss_indices[0]
        
        # 4. Combine results using Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        rrf_k = 60  # RRF constant
        
        for rank, idx in enumerate(bm25_top_indices):
            if idx not in rrf_scores:
                rrf_scores[idx] = 0
            rrf_scores[idx] += 1.0 / (rrf_k + rank + 1)
            
        for rank, idx in enumerate(faiss_top_indices):
            if idx not in rrf_scores:
                rrf_scores[idx] = 0
            rrf_scores[idx] += 1.0 / (rrf_k + rank + 1)
        
        # Sort by RRF score and get top-k
        sorted_indices = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:k]
        
        results = [self.metadata[idx] for idx in sorted_indices if idx < len(self.metadata)]
        print(f"Hybrid search returned {len(results)} candidates (BM25 + FAISS with RRF)")
        
        return results

    def rerank_with_full_data(self, query: str, candidates: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Use LLM to rerank candidates with FULL assessment data (name, description, duration, test_type).
        """
        if not self.llm:
            return candidates[:top_n]
            
        # Construct detailed candidate info
        candidates_text = ""
        for i, cand in enumerate(candidates):
            name = cand.get('name', 'Unknown')
            desc = cand.get('description', 'No description')[:200]  # Limit description length
            duration = cand.get('duration', 0)
            test_types = ', '.join(cand.get('test_type', []))
            remote = cand.get('remote_support', 'Unknown')
            
            candidates_text += f"""
ID {i}: {name}
  - Type: {test_types}
  - Duration: {duration} mins
  - Remote: {remote}
  - Description: {desc}
"""
            
        template = """
        You are an expert SHL assessment recommender acting for a specific client.
        
        User Query: "{query}"
        
        Available Assessments:
        {candidates}
        
        SELECTION CRITERIA (Client Specific Priorities):
        1. **Specific Tool/Skill Verification**: HIGHEST PRIORITY. If the query mentions specific tools (Excel, Java, Selenium, SQL), ALWAYS prioritize assessments that test those EXACT tools over general role assessments.
           - Example: Query "Marketing Manager with Excel" -> Prioritize "Microsoft Excel" over "Marketing Manager Solution".
        2. **Exact Skill Match**: Look for assessments that match specific hard skills mentioned (e.g., "Digital Advertising", "SEO", "Automata").
        3. **Role Relevance**: Use general role assessments (e.g., "Sales Solution") ONLY if specific skill tests are not available or as secondary options.
        4. **Soft Skills**: Include behavioral tests (OPQ, Communication) only if explicitly requested or to round out a technical profile.
        
        The client prefers specific, verifiable skill tests.
        
        Select the TOP {top_n} most relevant assessments.
        Return ONLY a JSON array of selected IDs. Example: [0, 3, 7, 2, 5, 8, 1, 4, 6, 9]
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        try:
            print(f"Reranking {len(candidates)} candidates with full data...")
            response = chain.invoke({
                "query": query,
                "candidates": candidates_text,
                "top_n": top_n
            })
            
            text = response.content.replace("```json", "").replace("```", "").strip()
            selected_ids = json.loads(text)
            print(f"LLM Selected IDs: {selected_ids}")
            
            final_results = []
            for idx in selected_ids:
                try:
                    idx = int(idx)
                    if 0 <= idx < len(candidates):
                        final_results.append(candidates[idx])
                except ValueError:
                    continue
            
            if len(final_results) < 1:
                return candidates[:top_n]
                
            return final_results[:top_n]
            
        except Exception as e:
            print(f"Reranking failed: {e}")
            return candidates[:top_n]
    
    def recommend(self, query: str, top_n: int = 10) -> List[Dict]:
        """
        Full pipeline: Query Expansion -> Hybrid Search (BM25+FAISS) -> LLM Rerank with Full Data
        """
        # Step 1 & 2: Hybrid search (includes query expansion)
        candidates = self.hybrid_search(query, k=20)
        
        # Step 3: Rerank with full candidate data
        results = self.rerank_with_full_data(query, candidates, top_n=top_n)
        
        return results

    # Keep old methods for backward compatibility
    def search(self, query, k=100, apply_filters=True):
        """Legacy search method - redirects to hybrid_search."""
        return self.hybrid_search(query, k=k)
    
    def rerank(self, query, candidates, top_n=10):
        """Legacy rerank method - redirects to rerank_with_full_data."""
        return self.rerank_with_full_data(query, candidates, top_n=top_n)

if __name__ == "__main__":
    # Test
    engine = RecommendationEngine()
    
    # Test query
    query = "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes."
    print(f"\n--- Testing: {query[:80]}... ---")
    
    results = engine.recommend(query, top_n=10)
    print(f"\nTop 10 Recommendations:")
    for i, item in enumerate(results):
        print(f"{i+1}. {item['name']} ({item.get('duration', '?')} mins) - {', '.join(item.get('test_type', []))}")
