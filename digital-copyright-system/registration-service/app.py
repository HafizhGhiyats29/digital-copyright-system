from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.metadata_store import (
    create_metadata,
    get_all_metadata,
    update_metadata,
    delete_metadata
)

app = FastAPI()

# ======================
# CORS (biar React bisa akses)
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# ROOT
# ======================
@app.get("/")
def root():
    return {"message": "Registration Service API jalan"}

# ======================
# CREATE
# ======================
@app.post("/metadata")
def create(data: dict):
    result = create_metadata(data)
    return {"id": str(result.inserted_id)}

# ======================
# READ
# ======================
@app.get("/metadata")
def read():
    data = get_all_metadata()
    result = []

    for d in data:
        d["_id"] = str(d["_id"])
        result.append(d)

    return result

# ======================
# UPDATE
# ======================
@app.put("/metadata/{id}")
def update(id: str, data: dict):
    update_metadata(id, data)
    return {"message": "updated"}

# ======================
# DELETE
# ======================
@app.delete("/metadata/{id}")
def delete(id: str):
    delete_metadata(id)
    return {"message": "deleted"}