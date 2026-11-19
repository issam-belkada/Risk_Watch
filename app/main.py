from fastapi import FastAPI

app = FastAPI(title="RiskWatch", version="0.1.0")


@app.get("/health", tags=["Santé"])
def health():
    return {"status": "ok"}