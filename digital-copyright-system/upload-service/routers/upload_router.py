from fastapi import APIRouter, UploadFile, File, HTTPException  # import fastapi
from utils.image_validator import validate_image  # import validator
from services.web_search_client import send_to_web_search  # import service
from schemas.response_schema import UploadResponse  # import schema
from utils.logger import logger  # import logger
from config.settings import MAX_FILE_SIZE  # import config
from services.feature_client import get_embedding
from services.similarity_client import send_to_similarity  # 🔥 TAMBAH INI
import uuid  # library membuat request id


router = APIRouter()  # membuat router


@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):

    # membuat request id
    request_id = str(uuid.uuid4())

    logger.info(f"[{request_id}] Upload request received")

    # validasi tipe file
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        logger.warning(f"[{request_id}] Unsupported file type: {file.content_type}")
        raise HTTPException(status_code=400, detail="Format gambar tidak didukung")

    # membaca file ke RAM
    file_bytes = await file.read()

    logger.info(f"[{request_id}] File name: {file.filename}")
    logger.info(f"[{request_id}] File size: {len(file_bytes)} bytes")

    # cek ukuran file
    if len(file_bytes) > MAX_FILE_SIZE:
        logger.warning(f"[{request_id}] File too large")
        raise HTTPException(status_code=400, detail="File terlalu besar")

    # validasi gambar
    validate_image(file_bytes)

    logger.info(f"[{request_id}] Image validation passed")

    # 1. ambil embedding original
    original_embedding = await get_embedding(file_bytes)

    # 2. web search
    web_result = await send_to_web_search(file_bytes)

    web_matches = web_result.get("matches", [])  # 🔥 penting (list)

    # 3. 🔥 similarity
    similarity_result = await send_to_similarity(
        original_embedding,
        web_matches
    )

    return {
    "status": "processed",
    "original_embedding": original_embedding,
    "web_search_result": web_result,
    "similarity_result": similarity_result  # 🔥 TAMBAH INI
    }