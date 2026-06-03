from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.rag_service import find_similar_errors, generate_suggestion

app = FastAPI(
    title="Zero-Trust TraceRAG Ingestion Engine",
    description="""
    ### Autonomous Semantic Error Resolution & Diagnosis Service
    
    This microservice exposes the orchestration engine for the log processing pipeline:
    * **Semantic Clustering:** Accepts raw stack traces, calculates cosine similarity on serverless vector storage (`pgvector`), and groups historic cases.
    * **Agentic Diagnosis:** Feeds targeted historical contexts to a local LLM under low temperature configurations to output structured JSON remedies.
    * **Defensive Boundary:** Operates inside an explicit parsing layer designed to isolate and sanitize unstructured model outputs.
    """,
    version="0.1.0"
)

class QueryRequest(BaseModel):
    error_log: str

@app.post("/query")
def analyze_error(
    query: QueryRequest
    ):
    try:
        err_log = query.error_log
        print("1")
        similar_cases = find_similar_errors(err_log)
        print("2")
        response = generate_suggestion(err_log, similar_cases)
        return {
            "similar_cases": similar_cases,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
