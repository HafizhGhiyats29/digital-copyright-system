from pydantic import BaseModel, Field  # Mengimpor BaseModel dan Field untuk schema validasi
from typing import Optional  # Mengimpor Optional untuk field opsional


class ThresholdConfig(BaseModel):  # Schema custom threshold dari user
    high: float = Field(..., ge=0.0, le=1.0)  # Threshold high harus di antara 0 sampai 1
    medium: float = Field(..., ge=0.0, le=1.0)  # Threshold medium harus di antara 0 sampai 1
    low: float = Field(..., ge=0.0, le=1.0)  # Threshold low harus di antara 0 sampai 1


class DecisionRequest(BaseModel):  # Schema request ke decision-engine
    overall_score: float = Field(..., ge=0.0, le=1.0)  # Score utama dari similarity-service
    clip_score: Optional[float] = Field(None, ge=0.0, le=1.0)  # Score CLIP kandidat terbaik
    cnn_score: Optional[float] = Field(None, ge=0.0, le=1.0)  # Score CNN kandidat terbaik
    preset: Optional[str] = None  # Preset threshold, contoh strict/balanced/sensitive
    thresholds: Optional[ThresholdConfig] = None  # Custom threshold dari user


class DecisionDetail(BaseModel):  # Schema detail keputusan
    status: str  # Status keputusan
    risk_level: str  # Level risiko
    requires_review: bool  # Apakah perlu review manual
    reason: str  # Alasan keputusan


class DecisionResponse(BaseModel):  # Schema response decision-engine
    overall_score: float  # Score utama yang sudah diproses
    clip_score: Optional[float] = None  # Score CLIP kandidat terbaik jika tersedia
    cnn_score: Optional[float] = None  # Score CNN kandidat terbaik jika tersedia
    decision: DecisionDetail  # Detail keputusan
