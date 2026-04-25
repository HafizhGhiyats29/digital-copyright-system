from pydantic import BaseModel  # Import BaseModel untuk schema validasi
from typing import List, Optional, Dict, Any  # Import tipe data


class FeatureResult(BaseModel):  # Schema hasil feature extraction original
    status: str  # Status feature extraction
    clip_embedding: List[float]  # Embedding CLIP original
    cnn_embedding: List[float]  # Embedding CNN original


class MatchItem(BaseModel):  # Schema item hasil web search
    image_url: str  # URL gambar kandidat
    source_url: Optional[str] = None  # URL sumber kandidat
    title: Optional[str] = None  # Judul kandidat
    clip_embedding: List[float]  # Embedding CLIP kandidat
    cnn_embedding: List[float]  # Embedding CNN kandidat


class WebSearchResult(BaseModel):  # Schema hasil web search
    found_on_web: bool  # Status apakah hasil web ditemukan
    matches: List[MatchItem]  # List kandidat gambar


class UploadResponse(BaseModel):  # Schema response upload
    status: str  # Status proses upload
    original_feature: FeatureResult  # Hasil embedding original
    web_search_result: WebSearchResult  # Hasil web search
    similarity_result: Optional[Dict[str, Any]] = None  # Hasil similarity service