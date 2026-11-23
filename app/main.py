from fastapi import FastAPI

from app.routers import auth, users

app = FastAPI(title="RiskWatch", version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/health", tags=["Santé"])
def health():
    return {"status": "ok"}