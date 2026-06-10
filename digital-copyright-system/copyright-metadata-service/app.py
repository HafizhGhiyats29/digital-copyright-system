from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from models.metadata_model import (
    EmbeddingReferenceUpdate,
    MetadataCreate,
    MetadataResponse,
    MetadataUpdate,
)
from utils.internal_auth import require_internal_api_key
from services.metadata_store import (
    DuplicateMetadataError,
    check_storage_health,
    create_metadata,
    delete_metadata,
    get_all_metadata,
    get_metadata_by_id,
    migrate_json_to_mongodb,
    update_metadata,
)


app = FastAPI(title="Copyright Metadata Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "copyright-metadata-service",
        "storage": check_storage_health(),
    }


@app.get("/")
def root():
    return {"message": "Copyright Metadata Service API jalan"}


@app.post("/metadata/migrate-json-to-mongodb", dependencies=[Depends(require_internal_api_key)])
def migrate_json_metadata_to_mongodb():
    return migrate_json_to_mongodb()


@app.post(
    "/metadata",
    response_model=MetadataResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_internal_api_key)],
)
def create(data: MetadataCreate):
    try:
        return create_metadata(data.model_dump(exclude_none=True, mode="json"))
    except DuplicateMetadataError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@app.get("/metadata", response_model=list[MetadataResponse])
def read_all():
    return get_all_metadata()


@app.get("/metadata/{metadata_id}", response_model=MetadataResponse)
def read_by_id(metadata_id: str):
    item = get_metadata_by_id(metadata_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not found",
        )
    return item


@app.put("/metadata/{metadata_id}", response_model=MetadataResponse, dependencies=[Depends(require_internal_api_key)])
def update(metadata_id: str, data: MetadataUpdate):
    payload = data.model_dump(exclude_unset=True, mode="json")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    item = update_metadata(metadata_id, payload)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not found",
        )
    return item


@app.patch("/metadata/{metadata_id}/embedding", response_model=MetadataResponse, dependencies=[Depends(require_internal_api_key)])
def update_embedding_reference(metadata_id: str, data: EmbeddingReferenceUpdate):
    payload = data.model_dump(exclude_unset=True)

    item = update_metadata(metadata_id, payload)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not found",
        )
    return item


@app.delete("/metadata/{metadata_id}", dependencies=[Depends(require_internal_api_key)])
def delete(metadata_id: str):
    deleted = delete_metadata(metadata_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not found",
        )
    return {"message": "deleted", "id": metadata_id}




