from pydantic import BaseModel
from typing import List, Optional


class MatchItem(BaseModel):
    image_url: str
    source_url: Optional[str] = None
    title: Optional[str] = None
    embedding: List[float]


class WebSearchResult(BaseModel):
    found_on_web: bool
    matches: List[MatchItem]


class UploadResponse(BaseModel):
    status: str
    original_embedding: List[float]
    web_search_result: WebSearchResult
    similarity_result: Optional[dict] = None