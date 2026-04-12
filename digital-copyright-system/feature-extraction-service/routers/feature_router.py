from fastapi import APIRouter, UploadFile, File
from services.feature_service import extract_embedding
from schemas.feature_schema import FeatureResponse

router = APIRouter()


@router.post("/extract", response_model=FeatureResponse)
async def extract_feature(image: UploadFile = File(...)):

    image_bytes = await image.read()

    embedding = extract_embedding(image_bytes)

    return {"embedding": embedding}