from pydantic import BaseModel

class SearchResponse(BaseModel):

    found_on_web: bool
    similar_images: list