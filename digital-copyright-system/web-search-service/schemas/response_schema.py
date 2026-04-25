from pydantic import BaseModel  # Import BaseModel dari Pydantic untuk schema validasi
from typing import List  # Import List untuk tipe data list


class MatchItem(BaseModel):  # Schema untuk setiap item hasil pencarian
    image_url: str  # URL gambar kandidat dari hasil web search
    source_url: str | None  # URL sumber gambar, bisa None jika tidak ada
    title: str | None  # Judul hasil pencarian, bisa None jika tidak ada
    clip_embedding: List[float]  # Embedding CLIP untuk makna visual gambar
    cnn_embedding: List[float]  # Embedding CNN untuk detail visual gambar


class SearchResponse(BaseModel):  # Schema response utama web search
    found_on_web: bool  # Status apakah ditemukan hasil di web
    matches: List[MatchItem]  # List kandidat gambar hasil web search