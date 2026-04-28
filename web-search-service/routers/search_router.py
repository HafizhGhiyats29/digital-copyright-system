from fastapi import APIRouter, UploadFile, File  # import FastAPI tools
from services.web_search_client import search_image  # import service utama
from schemas.response_schema import SearchResponse  # import schema response

router = APIRouter()  # membuat router


@router.post("/search", response_model=SearchResponse)  # endpoint + schema
async def search(image: UploadFile = File(...)):  # menerima file upload

    image_bytes = await image.read()  # membaca file menjadi bytes

    result = await search_image(image_bytes)  # kirim ke service utama

    return result  # return hasil (akan divalidasi oleh schema)