from fastapi import FastAPI
from routers.search_router import router


app = FastAPI(title="Web Search Service")

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}