from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI(
    title="Approval Service",
    description="API para gerenciar aprovações de ingestão de dados.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["approvals"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the Approval Service API"}


@app.get("/health")
def health():
    return {"status": "ok"}