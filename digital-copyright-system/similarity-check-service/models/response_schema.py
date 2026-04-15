from pydantic import BaseModel  # validasi


class SimilarityRequest(BaseModel):
    embedding: list
    web_matches: list