from pydantic import BaseModel
from typing import List


class FeatureResponse(BaseModel):
    embedding: List[float]