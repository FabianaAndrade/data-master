from fastapi import FastAPI
from app.api import router

app = FastAPI(
    title="Approval Service",
    description="API para gerenciar aprovações de ingestão de dados.",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1", tags=["ingestions"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Approval Service API"}