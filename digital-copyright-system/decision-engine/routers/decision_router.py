from fastapi import APIRouter, HTTPException, Depends  # Mengimpor router dan HTTPException dari FastAPI
from schemas.decision_schema import DecisionRequest, DecisionResponse  # Mengimpor schema request dan response
from services.decision_service import build_decision  # Mengimpor service decision
from utils.logger import logger
from utils.internal_auth import require_internal_api_key  # Mengimpor logger


router = APIRouter()  # Membuat router FastAPI


@router.post("/decision", response_model=DecisionResponse, dependencies=[Depends(require_internal_api_key)])  # Endpoint decision-engine
async def create_decision(request: DecisionRequest):  # Fungsi menerima request decision
    try:  # Memulai error handling
        logger.info(  # Log score yang diterima
            f"Decision request received with overall={request.overall_score}, "
            f"clip={request.clip_score}, cnn={request.cnn_score}"
        )  # Menutup logger

        result = build_decision(  # Membuat decision berdasarkan score dan threshold
            overall_score=request.overall_score,  # Mengirim overall_score
            clip_score=request.clip_score,  # Mengirim clip_score kandidat terbaik
            cnn_score=request.cnn_score,  # Mengirim cnn_score kandidat terbaik
            preset=request.preset,  # Mengirim preset dari user
            custom_thresholds=request.thresholds  # Mengirim custom threshold dari user
        )  # Menutup pemanggilan build_decision

        return result  # Mengembalikan hasil decision

    except ValueError as e:  # Menangkap error validasi threshold
        logger.warning(f"Invalid decision request: {str(e)}")  # Log request tidak valid
        raise HTTPException(status_code=400, detail=str(e))  # Mengembalikan error 400 ke client


