from fastapi import APIRouter, UploadFile, File, HTTPException  # Import komponen FastAPI
from utils.image_validator import validate_image  # Import validator gambar
from services.web_search_client import send_to_web_search  # Import client web search
from schemas.response_schema import UploadResponse  # Import schema response
from utils.logger import logger  # Import logger
from config.settings import MAX_FILE_SIZE  # Import batas ukuran file
from services.feature_client import get_embedding  # Import client feature extraction
from services.similarity_client import send_to_similarity  # Import client similarity service
import uuid  # Import uuid untuk membuat request id unik


router = APIRouter()  # Membuat router FastAPI


@router.post("/upload", response_model=UploadResponse)  # Endpoint upload gambar
async def upload_image(file: UploadFile = File(...)):  # Fungsi menerima file dari user
    request_id = str(uuid.uuid4())  # Membuat request id unik

    logger.info(f"[{request_id}] Upload request received")  # Log request diterima

    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:  # Validasi tipe file
        logger.warning(f"[{request_id}] Unsupported file type: {file.content_type}")  # Log tipe file salah
        raise HTTPException(status_code=400, detail="Format gambar tidak didukung")  # Return error format

    file_bytes = await file.read()  # Membaca file menjadi bytes

    logger.info(f"[{request_id}] File name: {file.filename}")  # Log nama file
    logger.info(f"[{request_id}] File size: {len(file_bytes)} bytes")  # Log ukuran file

    if len(file_bytes) > MAX_FILE_SIZE:  # Mengecek apakah file terlalu besar
        logger.warning(f"[{request_id}] File too large")  # Log file terlalu besar
        raise HTTPException(status_code=400, detail="File terlalu besar")  # Return error ukuran file

    validate_image(file_bytes)  # Validasi isi file benar-benar gambar

    logger.info(f"[{request_id}] Image validation passed")  # Log validasi berhasil

    original_feature = await get_embedding(file_bytes)  # Ambil CLIP + CNN embedding dari gambar original

    original_clip_embedding = original_feature["clip_embedding"]  # Ambil embedding CLIP original
    original_cnn_embedding = original_feature["cnn_embedding"]  # Ambil embedding CNN original

    web_result = await send_to_web_search(file_bytes)  # Kirim gambar ke web-search-service

    web_matches = web_result.get("matches", [])  # Ambil list kandidat dari web search

    similarity_result = await send_to_similarity(  # Kirim data ke similarity-service
        original_clip_embedding,  # Embedding CLIP original
        original_cnn_embedding,  # Embedding CNN original
        web_matches  # Kandidat web yang sudah punya CLIP + CNN embedding
    )  # Menutup pemanggilan similarity

    return {  # Return response ke user
        "status": "processed",  # Status proses
        "original_feature": original_feature,  # Embedding original CLIP + CNN
        "web_search_result": web_result,  # Hasil web search
        "similarity_result": similarity_result  # Hasil similarity
    }  # Menutup dictionary response