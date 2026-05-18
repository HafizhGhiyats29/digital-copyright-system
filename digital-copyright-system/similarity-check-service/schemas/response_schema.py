from pydantic import BaseModel  # Membuat schema validasi request/response
from typing import List, Optional  # Tipe data List dan Optional


class WebMatchItem(BaseModel):  # Schema untuk satu kandidat gambar dari web-search-service
    image_url: str  # URL gambar kandidat
    source_url: Optional[str] = None  # URL sumber gambar, boleh kosong
    title: Optional[str] = None  # Judul gambar, boleh kosong
    clip_embedding: List[float]  # Embedding CLIP kandidat
    cnn_embedding: List[float]  # Embedding CNN kandidat


class SimilarityRequest(BaseModel):  # Schema request similarity-service
    clip_embedding: List[float]  # Embedding CLIP gambar original
    cnn_embedding: List[float]  # Embedding CNN gambar original
    web_matches: List[WebMatchItem]  # List kandidat gambar dari web-search-service


class EmbeddingInsertRequest(BaseModel):
    metadata_id: str
    clip_embedding: List[float]
    cnn_embedding: List[float]
    embedding_version: str = "clip-cnn-v1"
