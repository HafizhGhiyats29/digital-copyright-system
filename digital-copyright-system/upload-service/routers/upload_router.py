from fastapi import APIRouter, UploadFile, File, HTTPException, Form  # Import FastAPI tools
from typing import Optional  # Import Optional untuk parameter opsional
from utils.image_validator import validate_image  # Import validator gambar
from services.web_search_client import send_to_web_search  # Import client web-search
from schemas.response_schema import UploadResponse  # Import schema response
from utils.logger import logger  # Import logger
from config.settings import MAX_FILE_SIZE  # Import batas ukuran file
from services.feature_client import get_embedding  # Import client feature-service
from services.similarity_client import send_to_similarity  # Import client similarity-service
from services.decision_client import send_to_decision  # Import client decision-engine
import uuid  # Import uuid untuk request id


router = APIRouter()  # Membuat router FastAPI


@router.post("/upload", response_model=UploadResponse)  # Endpoint upload gambar
async def upload_image(  # Fungsi menerima upload gambar dan threshold
    file: UploadFile = File(...),  # File gambar wajib dikirim
    preset: Optional[str] = Form(None),  # Preset threshold opsional
    high_threshold: Optional[float] = Form(None),  # Custom high threshold opsional
    medium_threshold: Optional[float] = Form(None),  # Custom medium threshold opsional
    low_threshold: Optional[float] = Form(None)  # Custom low threshold opsional
):  # Menutup parameter function
    request_id = str(uuid.uuid4())  # Membuat request id unik

    logger.info(f"[{request_id}] Upload request received")  # Log request diterima

    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:  # Validasi tipe file
        logger.warning(f"[{request_id}] Unsupported file type: {file.content_type}")  # Log tipe file tidak didukung
        raise HTTPException(status_code=400, detail="Format gambar tidak didukung")  # Return error 400

    file_bytes = await file.read()  # Membaca file menjadi bytes

    logger.info(f"[{request_id}] File name: {file.filename}")  # Log nama file
    logger.info(f"[{request_id}] File size: {len(file_bytes)} bytes")  # Log ukuran file

    if len(file_bytes) > MAX_FILE_SIZE:  # Mengecek ukuran file
        logger.warning(f"[{request_id}] File too large")  # Log file terlalu besar
        raise HTTPException(status_code=400, detail="File terlalu besar")  # Return error 400

    validate_image(file_bytes)  # Validasi isi gambar

    logger.info(f"[{request_id}] Image validation passed")  # Log gambar valid

    custom_thresholds = None  # Default tidak memakai custom threshold

    if preset:  # Jika user memilih preset, gunakan preset dan abaikan threshold manual
        logger.info(f"[{request_id}] Using threshold preset: {preset}")  # Log preset yang dipakai

    else:  # Jika preset tidak diisi, baru cek custom threshold
        threshold_values = [high_threshold, medium_threshold, low_threshold]  # Kumpulkan input threshold manual

        if any(value is not None for value in threshold_values):  # Jika salah satu threshold manual diisi
            if not all(value is not None for value in threshold_values):  # Jika tidak lengkap
             raise HTTPException(status_code=400, detail="Custom threshold harus lengkap: high, medium, low")  # Error threshold tidak lengkap

            custom_thresholds = {  # Buat custom threshold
                "high": high_threshold,  # Threshold high
                "medium": medium_threshold,  # Threshold medium
                "low": low_threshold  # Threshold low
            }  # Menutup dictionary custom threshold

            logger.info(f"[{request_id}] Using custom thresholds: {custom_thresholds}")  # Log custom threshold

    original_feature = await get_embedding(file_bytes)  # Ambil CLIP + CNN embedding original

    original_clip_embedding = original_feature["clip_embedding"]  # Ambil CLIP embedding original
    original_cnn_embedding = original_feature["cnn_embedding"]  # Ambil CNN embedding original

    web_result = await send_to_web_search(file_bytes)  # Kirim gambar ke web-search-service

    web_matches = web_result.get("matches", [])  # Ambil kandidat external dari web-search

    similarity_result = await send_to_similarity(  # Kirim data ke similarity-service
        original_clip_embedding,  # CLIP embedding original
        original_cnn_embedding,  # CNN embedding original
        web_matches  # Kandidat external
    )  # Menutup similarity call

    overall_score = similarity_result.get("overall_score", 0.0)  # Ambil overall_score dari similarity-service

    decision_result = await send_to_decision(  # Kirim overall_score ke decision-engine
        overall_score=overall_score,  # Score utama similarity
        preset=preset,  # Preset dari frontend
        thresholds=custom_thresholds  # Custom threshold dari frontend
    )  # Menutup decision call

    return {  # Mengembalikan response final ke frontend
        "status": "processed",  # Status proses
        "original_feature": original_feature,  # Embedding original
        "web_search_result": web_result,  # Hasil web search
        "similarity_result": similarity_result,  # Hasil similarity
        "decision_result": decision_result  # Hasil decision-engine
    }  # Menutup response dictionary