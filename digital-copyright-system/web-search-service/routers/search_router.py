from fastapi import APIRouter, UploadFile, File, Depends  # import FastAPI tools
from services.web_search_client import search_image  # import service utama
from schemas.response_schema import SearchResponse
from utils.internal_auth import require_internal_api_key  # import schema response

router = APIRouter()  # membuat router


@router.post("/search", response_model=SearchResponse, dependencies=[Depends(require_internal_api_key)])  # endpoint + schema
async def search(image: UploadFile = File(...)):  # menerima file upload

    image_bytes = await image.read()  # membaca file menjadi bytes

    result = await search_image(image_bytes)  # kirim ke service utama

    return result  # return hasil (akan divalidasi oleh schema)

