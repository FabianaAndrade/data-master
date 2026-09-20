from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI(
    title="Ingestion Service",
    description="API middleware para gerenciar ingestões de dados.",
    version="1.0.0",
)

Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, tags=["ingestion"])


@app.get("/")
def read_root():
    return {"message": "Ingestion service is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
