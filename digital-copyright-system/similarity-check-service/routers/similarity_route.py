from fastapi import APIRouter, HTTPException  # Mengimpor APIRouter dari FastAPI
from schemas.response_schema import EmbeddingInsertRequest, SimilarityRequest  # Mengimpor schema request similarity
from services.milvus_client import delete_embedding_by_metadata_id, insert_embedding  # Insert/delete embedding ke Milvus
from services.similarity_service import compute_similarity  # Mengimpor service utama similarity


router = APIRouter()  # Membuat router FastAPI


@router.post("/similarity")  # Membuat endpoint POST /similarity
async def similarity_check(request: SimilarityRequest):  # Fungsi endpoint menerima request similarity
    result = await compute_similarity(  # Menjalankan proses similarity
        request.clip_embedding,  # Mengirim embedding CLIP gambar input
        request.cnn_embedding,  # Mengirim embedding CNN gambar input
        request.web_matches  # Mengirim kandidat web external
    )  # Menutup pemanggilan compute_similarity

    return result  # Mengembalikan hasil final ke client/upload-service


@router.post("/embeddings")
async def create_embedding(request: EmbeddingInsertRequest):
    try:
        return insert_embedding(
            metadata_id=request.metadata_id,
            clip_embedding=request.clip_embedding,
            cnn_embedding=request.cnn_embedding,
            embedding_version=request.embedding_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@router.delete("/embeddings/{metadata_id}")
async def delete_embedding(metadata_id: str):
    try:
        return delete_embedding_by_metadata_id(metadata_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
