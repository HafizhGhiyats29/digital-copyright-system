from fastapi import APIRouter, HTTPException  # Mengimpor router dan HTTPException dari FastAPI
from schemas.decision_schema import DecisionRequest, DecisionResponse  # Mengimpor schema request dan response
from services.decision_service import build_decision  # Mengimpor service decision
from utils.logger import logger  # Mengimpor logger


router = APIRouter()  # Membuat router FastAPI


@router.post("/decision", response_model=DecisionResponse)  # Endpoint decision-engine
async def create_decision(request: DecisionRequest):  # Fungsi menerima request decision
    try:  # Memulai error handling
        logger.info(f"Decision request received with score: {request.overall_score}")  # Log score yang diterima

        result = build_decision(  # Membuat decision berdasarkan score dan threshold
            overall_score=request.overall_score,  # Mengirim overall_score
            preset=request.preset,  # Mengirim preset dari user
            custom_thresholds=request.thresholds  # Mengirim custom threshold dari user
        )  # Menutup pemanggilan build_decision

        return result  # Mengembalikan hasil decision

    except ValueError as e:  # Menangkap error validasi threshold
        logger.warning(f"Invalid decision request: {str(e)}")  # Log request tidak valid
        raise HTTPException(status_code=400, detail=str(e))  # Mengembalikan error 400 ke client