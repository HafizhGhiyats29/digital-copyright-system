from fastapi import APIRouter, UploadFile, File
from services.web_search_client import search_image

router = APIRouter()


@router.post("/search")
async def search():

    result = await search_image()

    return result