from pydantic import BaseModel  # Base schema dari Pydantic
from typing import List  # Tipe data list


class FeatureResponse(BaseModel):  # Schema response feature extraction
    status: str  # Status proses
    clip_embedding: List[float]  # Embedding CLIP
    cnn_embedding: List[float]  # Embedding CNN