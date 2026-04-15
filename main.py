from fastapi import FastAPI

app = FastAPI(
    title="PDF-extractor API",
    version="1.0",
    description="API for extracting passport data from pdf files",
)


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
