from fastapi import FastAPI  # framework API
from routers.similarity_route import router  # import router

app = FastAPI(title="Similarity Check Service") 
# init app

app.include_router(router) 

@app.get("/health")
def health():
    return {"status": "ok"} 