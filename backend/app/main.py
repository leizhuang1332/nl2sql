from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import query, metadata, history

app = FastAPI(
    title="NL2SQL API",
    description="Natural Language to SQL Query System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(metadata.router, prefix="/api", tags=["metadata"])
app.include_router(history.router, prefix="/api", tags=["history"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nl2sql"}
