from fastapi import FastAPI
from .app.api import router as api_router

app = FastAPI(
    title="Metadata Service",
    description="API para gerenciar metadados de tabelas e seu versionamento.",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1", tags=["ingestions"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Metadata Service API"}
