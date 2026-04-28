from fastapi import FastAPI
from routers.feature_router import router

app = FastAPI(title="Feature Extraction Service")

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}