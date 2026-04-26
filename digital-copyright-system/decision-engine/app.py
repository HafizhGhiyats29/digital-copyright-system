from fastapi import FastAPI  # import FastAPI
from routers.decision_router import router as decision_router  # import decision router


app = FastAPI(title="Upload Service")  # membuat instance FastAPI


app.include_router(decision_router)  # menambahkan decision router ke aplikasi


@app.get("/health")  # endpoint health check
def health():
    return {"status": "ok"}