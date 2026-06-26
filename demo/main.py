import os
import requests
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv() 

app = FastAPI(title="Demo App — Intentionally Broken")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Engine URL (the TraceRAG backend, NOT Ollama)
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://127.0.0.1:8000")
def report_error(message: str, trace: str, sanitized: str, service: str):
    payload = {
        "message": message,
        "stack_trace": trace,
        "sanitized_trace": sanitized,
        "service_name": service
    }
    print(f"\n--- SENDING TO AI ENGINE ---\n{payload['message']}\n----------------------------\n")
    try:
        requests.post(f"{AI_ENGINE_URL}/errors/log-error", json=payload, timeout=30)
    except Exception as e:
        print(f"Failed to report error to AI Engine: {e}")
        pass  

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace = traceback.format_exc()
    report_error(
        message=f"{type(exc).__name__}: {str(exc)}",
        trace=trace,
        sanitized=str(exc),
        service="demo-service"
    )
    return JSONResponse(
        status_code=500, 
        content={"error": str(exc), "status": "Error logged to TraceRAG"},
        headers={"Access-Control-Allow-Origin": "*"}
    )

# --- The Broken Endpoints ---

@app.get("/")
def health_check():
    return {"status": "Demo app is running"}

@app.get("/crash/null-pointer")
def null_pointer():
    user = None
    return user["email"]  # AttributeError — simulates NPE

@app.get("/crash/auth-failure")  
def auth_failure():
    raise ValueError("JWT token has expired during authentication")

@app.get("/crash/not-found")
def not_found():
    raise LookupError("User with id 99999 not found in database")

@app.get("/crash/memory")
def memory_error():
    raise MemoryError("Java heap space exhausted during report generation")

@app.get("/crash/db-timeout")
def db_timeout():
    raise TimeoutError("Database connection pool exhausted after 30000ms")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)