from fastapi import FastAPI
from backend.app.api.v1.router import router as api_router

app = FastAPI(
    title="PDF-extractor API",
    version="1.0",
    description="API for extracting passport data from pdf files",
)

app.include_router(api_router)

@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
