from fastapi import APIRouter  # router
from models.response_schema import SimilarityRequest  # schema
from services.similarity_service import compute_similarity  # service

router = APIRouter()


@router.post("/similarity")
async def similarity_check(request: SimilarityRequest):

    results = await compute_similarity(
        request.embedding,
        request.web_matches
    )

    return {
        "total": len(results),
        "results": results
    }