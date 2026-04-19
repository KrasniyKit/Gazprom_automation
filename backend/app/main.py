import json
import os
import urllib.request

from fastapi import FastAPI, HTTPException
from app.api.v1.router import router as api_router

app = FastAPI(
    title="PDF-extractor API",
    version="1.0",
    description="API for extracting passport data from pdf files",
)

app.include_router(api_router)


def _ollama_readiness() -> tuple[bool, str]:
    ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5vl:7b")

    try:
        with urllib.request.urlopen(f"{ollama_host}/api/tags", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return False, f"Ollama недоступна: {e}"

    models = {model.get("name") for model in payload.get("models", []) if model.get("name")}
    if model_name not in models:
        return False, f"Модель {model_name} не загружена в Ollama."
    return True, "ok"

@app.get("/health")
async def healthcheck():
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness():
    ready, reason = _ollama_readiness()
    if not ready:
        raise HTTPException(status_code=503, detail=reason)
    return {"status": "ready"}
