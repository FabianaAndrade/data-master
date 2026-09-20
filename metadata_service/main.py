from fastapi import FastAPI
from app.routes import router
from app.database import startup_db_seed
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="Metadata Service",
    description="API para gerenciar metadados de tabelas e seu versionamento.",
    version="1.0.0"
)

Instrumentator().instrument(app).expose(app)

app.include_router(router, tags=["ingestions"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Metadata Service API"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.on_event("startup")
def on_startup():
    startup_db_seed()