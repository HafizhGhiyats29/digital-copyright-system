from pydantic import BaseModel  # Import BaseModel untuk membuat schema response
from typing import List, Optional, Dict, Any  # Import tipe data yang dibutuhkan


class FeatureResult(BaseModel):  # Schema hasil feature extraction original
    status: str  # Status feature extraction

    # Aktifkan ini jika ingin embedding original ikut muncul di response
    # clip_embedding: List[float]  # Embedding CLIP original
    # cnn_embedding: List[float]  # Embedding CNN original


class MatchItem(BaseModel):  # Schema item hasil web search
    image_url: str  # URL gambar kandidat
    source_url: Optional[str] = None  # URL sumber kandidat
    title: Optional[str] = None  # Judul kandidat

    # Aktifkan ini jika ingin embedding kandidat web ikut muncul di response
    # clip_embedding: List[float]  # Embedding CLIP kandidat
    # cnn_embedding: List[float]  # Embedding CNN kandidat


class WebSearchResult(BaseModel):  # Schema hasil web search
    found_on_web: bool  # Status apakah hasil ditemukan di web
    matches: List[MatchItem]  # List kandidat gambar tanpa embedding jika field embedding dimatikan


class UploadResponse(BaseModel):  # Schema response akhir upload-service
    status: str  # Status proses upload
    original_feature: Optional[FeatureResult] = None  # Hasil feature extraction original tanpa embedding
    web_search_result: WebSearchResult  # Hasil web search tanpa embedding kandidat
    similarity_result: Optional[Dict[str, Any]] = None  # Hasil similarity-service
    decision_result: Optional[Dict[str, Any]] = None  # Hasil decision-engine