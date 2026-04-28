from fastapi import FastAPI  # import FastAPI
from routers.upload_router import router  # import router


app = FastAPI(title="Upload Service")  # membuat instance FastAPI


app.include_router(router)  # menambahkan router ke aplikasi


@app.get("/health")  # endpoint health check
def health():
    return {"status": "ok"}