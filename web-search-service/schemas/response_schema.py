from pydantic import BaseModel
from typing import List


class MatchItem(BaseModel):
    image_url: str
    source_url: str | None
    title: str | None
    embedding: List[float]  # 🔥 TAMBAHKAN INI


class SearchResponse(BaseModel):
    found_on_web: bool
    matches: List[MatchItem]