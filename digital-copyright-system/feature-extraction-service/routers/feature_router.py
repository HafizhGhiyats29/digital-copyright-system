from fastapi import APIRouter, UploadFile, File, HTTPException, Depends  # Komponen FastAPI untuk route upload
from schemas.feature_schema import FeatureResponse  # Schema response
from services.feature_service import extract_features  # Service utama extraction
from utils.logger import logger
from utils.internal_auth import require_internal_api_key  # Logger


router = APIRouter()  # Membuat router FastAPI


@router.post("/extract", response_model=FeatureResponse, dependencies=[Depends(require_internal_api_key)])  # Endpoint extract gambar
async def extract_image(file: UploadFile = File(...)):  # Menerima file gambar dari request
    try:  # Memulai error handling
        logger.info(f"Received file: {file.filename}")  # Log nama file

        image_bytes = await file.read()  # Membaca file menjadi bytes

        if not image_bytes:  # Mengecek file kosong
            raise HTTPException(status_code=400, detail="File kosong")  # Error jika file kosong

        result = await extract_features(image_bytes)  # Proses CLIP + CNN extraction

        return result  # Mengembalikan hasil extraction

    except HTTPException as e:  # Menangkap HTTPException
        raise e  # Lempar ulang HTTPException

    except Exception as e:  # Menangkap error umum
        logger.error(f"Feature extraction failed: {str(e)}")  # Log error
        raise HTTPException(status_code=500, detail="Feature extraction gagal")  # Return error 500

