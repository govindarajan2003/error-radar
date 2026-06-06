from fastapi import FastAPI
from api.routes import error_routes, query_routes

app = FastAPI(title="Zero-Trust TraceRAG")

app.include_router(error_routes.router)
app.include_router(query_routes.router)