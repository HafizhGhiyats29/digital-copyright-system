from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MetadataBase(BaseModel):
    check_id: Optional[str] = Field(default=None, description="ID hasil pengecekan plagiarisme yang menghasilkan metadata ini")
    ki_id: Optional[str] = Field(default=None, description="ID KI dari dataset sumber jika tersedia")
    ki_uuid: Optional[str] = Field(default=None, description="UUID KI dari dataset sumber jika tersedia")
    title: str = Field(..., min_length=1, description="Judul karya")
    description: Optional[str] = Field(default=None, description="Deskripsi karya")
    category: Optional[str] = Field(default=None, description="Kategori utama, contoh: HAK CIPTA")
    sub_category: Optional[str] = Field(default=None, description="Sub kategori, contoh: Karya Seni")
    copyright_category: Optional[str] = Field(default=None, description="Kategori hak cipta")
    copyright_sub_category: Optional[str] = Field(default=None, description="Sub kategori hak cipta")
    image_url: Optional[str] = Field(default=None, description="URL gambar karya")
    cloudinary_public_id: Optional[str] = Field(default=None, description="Public ID Cloudinary jika gambar disimpan di Cloudinary")
    milvus_collection: Optional[str] = Field(default=None, description="Nama collection Milvus untuk embedding karya")
    milvus_id: Optional[str] = Field(default=None, description="ID row Milvus yang menyimpan CLIP dan CNN embedding")
    embedding_version: Optional[str] = Field(default=None, description="Versi embedding/model yang digunakan")
    embedding_status: str = Field(default="pending", description="Status embedding: pending, ready, atau failed")


class MetadataCreate(MetadataBase):
    pass


class MetadataUpdate(BaseModel):
    check_id: Optional[str] = None
    ki_id: Optional[str] = None
    ki_uuid: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    copyright_category: Optional[str] = None
    copyright_sub_category: Optional[str] = None
    image_url: Optional[str] = None
    cloudinary_public_id: Optional[str] = None
    milvus_collection: Optional[str] = None
    milvus_id: Optional[str] = None
    embedding_version: Optional[str] = None
    embedding_status: Optional[str] = None


class EmbeddingReferenceUpdate(BaseModel):
    milvus_collection: Optional[str] = Field(default=None, description="Nama collection Milvus")
    milvus_id: Optional[str] = Field(default=None, description="ID row/vector di Milvus")
    embedding_version: Optional[str] = Field(default=None, description="Versi embedding/model")
    embedding_status: str = Field(..., description="Status embedding: pending, ready, atau failed")


class MetadataResponse(MetadataBase):
    id: str
    created_at: datetime
    updated_at: datetime
