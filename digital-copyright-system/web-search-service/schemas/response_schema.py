from pydantic import BaseModel
from typing import List


class ImageMatch(BaseModel):
    image_url: str
    source_url: str
    title: str


class SearchResponse(BaseModel):
    found_on_web: bool
    matches: List[ImageMatch]