from fastapi import APIRouter  # Import router FastAPI
from schemas.response_schema import SimilarityRequest  # Import schema request
from services.similarity_service import compute_similarity  # Import service similarity


router = APIRouter()  # Membuat router FastAPI


@router.post("/similarity")  # Endpoint similarity check
async def similarity_check(request: SimilarityRequest):  # Fungsi menerima request similarity
    results = await compute_similarity(  # Jalankan similarity service
        request.clip_embedding,  # Embedding CLIP original
        request.cnn_embedding,  # Embedding CNN original
        request.web_matches  # Kandidat dari web-search
    )  # Menutup pemanggilan compute_similarity

    return {  # Return response API
        "total": len(results),  # Jumlah hasil similarity
        "results": results  # List hasil similarity
    }  # Menutup dictionary