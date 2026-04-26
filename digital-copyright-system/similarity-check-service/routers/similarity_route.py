from fastapi import APIRouter  # Mengimpor APIRouter dari FastAPI
from schemas.response_schema import SimilarityRequest  # Mengimpor schema request similarity
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