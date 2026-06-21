from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import error_routes, query_routes

app = FastAPI(title="Zero-Trust TraceRAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(error_routes.router)
app.include_router(query_routes.router)