from datetime import datetime  # Import datetime untuk response schema metadata
from typing import Optional  # Import Optional untuk form yang tidak wajib diisi

import httpx  # Import HTTP client exception untuk orchestration delete
from fastapi import APIRouter, Body, File, Form, HTTPException, Request, UploadFile, status  # Import router, request, dan multipart tools FastAPI
from pydantic import BaseModel, Field  # Import schema untuk dokumentasi OpenAPI

from utils.proxy import build_target_url  # Import builder URL upstream
from utils.proxy import proxy_multipart_request, proxy_request  # Import helper proxy reusable


router = APIRouter(tags=["gateway"])  # Membuat router untuk endpoint gateway


class MetadataBase(BaseModel):  # Schema dasar metadata karya untuk dokumentasi gateway
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
    milvus_collection: Optional[str] = Field(default=None, description="Nama collection Milvus")
    milvus_id: Optional[str] = Field(default=None, description="ID row/vector di Milvus")
    embedding_version: Optional[str] = Field(default=None, description="Versi embedding/model")
    embedding_status: str = Field(default="pending", description="Status embedding: pending, ready, atau failed")


class MetadataCreate(MetadataBase):  # Schema create metadata
    pass


class MetadataUpdate(BaseModel):  # Schema update metadata parsial
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


class EmbeddingReferenceUpdate(BaseModel):  # Schema update khusus referensi embedding/Milvus
    milvus_collection: Optional[str] = Field(default=None, description="Nama collection Milvus")
    milvus_id: Optional[str] = Field(default=None, description="ID row/vector di Milvus")
    embedding_version: Optional[str] = Field(default=None, description="Versi embedding/model")
    embedding_status: str = Field(..., description="Status embedding: pending, ready, atau failed")


class MetadataResponse(MetadataBase):  # Schema response metadata
    id: str
    created_at: datetime
    updated_at: datetime


class RegisterMetadataRequest(BaseModel):  # Schema registrasi metadata setelah upload/check aman
    check_id: str = Field(..., description="ID hasil pengecekan dari endpoint upload")
    ki_id: Optional[str] = None
    ki_uuid: Optional[str] = None
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    copyright_category: Optional[str] = None
    copyright_sub_category: Optional[str] = None
    image_url: Optional[str] = None
    cloudinary_public_id: Optional[str] = None


class ReviewCheckRequest(BaseModel):  # Schema review manual check_id
    reason: Optional[str] = Field(default=None, description="Catatan/alasan reviewer")


@router.post("/upload")  # Endpoint gateway untuk upload gambar
async def upload(  # Handler request upload
    request: Request,  # Request asli dari client
    file: UploadFile = File(...),  # File gambar wajib dikirim dengan field bernama file
    preset: Optional[str] = Form(None),  # Preset threshold opsional
    high_threshold: Optional[float] = Form(None),  # Custom high threshold opsional
    medium_threshold: Optional[float] = Form(None),  # Custom medium threshold opsional
    low_threshold: Optional[float] = Form(None),  # Custom low threshold opsional
):  # Menutup parameter upload
    # Main pipeline entrypoint: upload-service orchestrates the full workflow.
    return await proxy_multipart_request(  # Forward multipart ke upload-service
        request,  # Request asli dari client
        "upload-service",  # Nama upstream service tujuan
        "/upload",  # Path endpoint upload-service
        "file",  # Nama field file sesuai kontrak upload-service
        file,  # File gambar dari client
        {  # Form data tambahan yang diteruskan ke upload-service
            "preset": preset,  # Preset threshold
            "high_threshold": high_threshold,  # Custom high threshold
            "medium_threshold": medium_threshold,  # Custom medium threshold
            "low_threshold": low_threshold,  # Custom low threshold
        },  # Menutup form data tambahan
    )  # Menutup proxy multipart upload


@router.post("/register-metadata")  # Endpoint gateway untuk registrasi metadata setelah cek plagiarisme
async def register_metadata(
    request: Request,  # Request asli dari client
    data: RegisterMetadataRequest = Body(...),  # Body schema untuk dokumentasi OpenAPI
):  # Handler proxy registrasi metadata aman
    return await proxy_request(  # Forward request ke upload-service sebagai orchestrator
        request,  # Request asli dari client
        "upload-service",  # Nama upstream service tujuan
        "/register-metadata",  # Path endpoint upload-service
    )  # Menutup proxy register metadata


@router.post("/review-check/{check_id}/approve")  # Endpoint gateway untuk approve hasil cek manual
async def approve_check(
    request: Request,  # Request asli dari client
    check_id: str,  # ID hasil pengecekan
    data: ReviewCheckRequest = Body(default_factory=ReviewCheckRequest),  # Body catatan review opsional
):  # Handler proxy approve review
    return await proxy_request(  # Forward request ke upload-service
        request,  # Request asli dari client
        "upload-service",  # Nama upstream service tujuan
        f"/review-check/{check_id}/approve",  # Path approve review
    )  # Menutup proxy approve review


@router.post("/review-check/{check_id}/reject")  # Endpoint gateway untuk reject hasil cek manual
async def reject_check(
    request: Request,  # Request asli dari client
    check_id: str,  # ID hasil pengecekan
    data: ReviewCheckRequest = Body(default_factory=ReviewCheckRequest),  # Body catatan review opsional
):  # Handler proxy reject review
    return await proxy_request(  # Forward request ke upload-service
        request,  # Request asli dari client
        "upload-service",  # Nama upstream service tujuan
        f"/review-check/{check_id}/reject",  # Path reject review
    )  # Menutup proxy reject review


@router.get("/metadata", response_model=list[MetadataResponse])  # Endpoint gateway untuk list metadata
async def metadata_collection(request: Request):  # Handler proxy list metadata
    return await proxy_request(  # Forward request ke copyright-metadata-service
        request,  # Request asli dari client
        "copyright-metadata-service",  # Nama upstream service tujuan
        "/metadata",  # Path endpoint metadata service
    )  # Menutup proxy metadata collection


@router.post(
    "/metadata",
    response_model=MetadataResponse,
    status_code=status.HTTP_201_CREATED,
)  # Endpoint gateway untuk create metadata
async def create_metadata_item(
    request: Request,  # Request asli dari client
    data: MetadataCreate = Body(...),  # Body schema untuk dokumentasi OpenAPI
):  # Handler proxy create metadata
    return await proxy_request(  # Forward request ke copyright-metadata-service
        request,  # Request asli dari client
        "copyright-metadata-service",  # Nama upstream service tujuan
        "/metadata",  # Path endpoint metadata service
    )  # Menutup proxy create metadata


@router.get("/metadata/{metadata_id}", response_model=MetadataResponse)  # Endpoint gateway untuk detail metadata
async def read_metadata_item(request: Request, metadata_id: str):  # Handler proxy detail metadata
    return await proxy_request(  # Forward request ke copyright-metadata-service
        request,  # Request asli dari client
        "copyright-metadata-service",  # Nama upstream service tujuan
        f"/metadata/{metadata_id}",  # Path endpoint item metadata
    )  # Menutup proxy metadata item


@router.put("/metadata/{metadata_id}", response_model=MetadataResponse)  # Endpoint gateway untuk update metadata
async def update_metadata_item(
    request: Request,  # Request asli dari client
    metadata_id: str,  # ID metadata
    data: MetadataUpdate = Body(...),  # Body schema untuk dokumentasi OpenAPI
):  # Handler proxy update metadata
    return await proxy_request(  # Forward request ke copyright-metadata-service
        request,  # Request asli dari client
        "copyright-metadata-service",  # Nama upstream service tujuan
        f"/metadata/{metadata_id}",  # Path endpoint item metadata
    )  # Menutup proxy metadata item


@router.patch("/metadata/{metadata_id}/embedding", response_model=MetadataResponse)  # Endpoint gateway untuk update referensi embedding
async def update_metadata_embedding(
    request: Request,  # Request asli dari client
    metadata_id: str,  # ID metadata
    data: EmbeddingReferenceUpdate = Body(...),  # Body schema update embedding
):  # Handler proxy update embedding
    return await proxy_request(  # Forward request ke copyright-metadata-service
        request,  # Request asli dari client
        "copyright-metadata-service",  # Nama upstream service tujuan
        f"/metadata/{metadata_id}/embedding",  # Path endpoint update embedding
    )  # Menutup proxy update embedding


@router.delete("/metadata/{metadata_id}")  # Endpoint gateway untuk delete metadata
async def delete_metadata_item(request: Request, metadata_id: str):  # Handler proxy delete metadata
    client = request.app.state.http_client  # Ambil client HTTP reusable
    cleanup = {  # Ringkasan cleanup lintas storage
        "cloudinary": {"skipped": True},
        "milvus": {"skipped": True},
        "metadata": {"deleted": False},
    }  # Menutup dict cleanup

    metadata_url = build_target_url("copyright-metadata-service", f"/metadata/{metadata_id}")  # URL metadata item
    vector_url = build_target_url("similarity-check-service", f"/embeddings/{metadata_id}")  # URL hapus vector Milvus
    cloudinary_url = build_target_url("upload-service", "/cloudinary/delete")  # URL hapus gambar Cloudinary

    try:  # Ambil metadata dulu agar tahu public_id Cloudinary
        metadata_response = await client.get(metadata_url)  # Request detail metadata
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Gagal mengambil metadata: {exc}") from exc

    if metadata_response.status_code == 404:  # Metadata tidak ada
        raise HTTPException(status_code=404, detail="Metadata not found")

    if metadata_response.status_code >= 400:  # Error upstream metadata
        raise HTTPException(status_code=metadata_response.status_code, detail=metadata_response.text)

    metadata = metadata_response.json()  # Parse metadata JSON
    public_id = metadata.get("cloudinary_public_id")  # Ambil public_id Cloudinary

    if public_id:  # Hapus gambar Cloudinary jika ada
        try:
            cloudinary_response = await client.post(cloudinary_url, json={"public_id": public_id})
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Gagal menghapus gambar Cloudinary: {exc}") from exc

        cleanup["cloudinary"] = {
            "skipped": False,
            "status_code": cloudinary_response.status_code,
            "response": cloudinary_response.json() if cloudinary_response.content else None,
        }

        if cloudinary_response.status_code >= 400:
            raise HTTPException(status_code=cloudinary_response.status_code, detail=cleanup)

    try:  # Hapus vector Milvus
        vector_response = await client.delete(vector_url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Gagal menghapus vector Milvus: {exc}") from exc

    cleanup["milvus"] = {
        "skipped": False,
        "status_code": vector_response.status_code,
        "response": vector_response.json() if vector_response.content else None,
    }

    if vector_response.status_code >= 400:
        raise HTTPException(status_code=vector_response.status_code, detail=cleanup)

    try:  # Terakhir hapus metadata
        delete_response = await client.delete(metadata_url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Gagal menghapus metadata: {exc}") from exc

    cleanup["metadata"] = {
        "deleted": delete_response.status_code < 400,
        "status_code": delete_response.status_code,
        "response": delete_response.json() if delete_response.content else None,
    }

    if delete_response.status_code >= 400:
        raise HTTPException(status_code=delete_response.status_code, detail=cleanup)

    return {
        "message": "metadata, vector Milvus, dan gambar Cloudinary berhasil dibersihkan",
        "id": metadata_id,
        "cleanup": cleanup,
    }


@router.delete("/metadata/{metadata_id}/vector")  # Endpoint gateway untuk hapus vector Milvus metadata
async def delete_metadata_vector(request: Request, metadata_id: str):  # Handler proxy hapus vector Milvus
    return await proxy_request(  # Forward request ke similarity-check-service
        request,  # Request asli dari client
        "similarity-check-service",  # Nama upstream service tujuan
        f"/embeddings/{metadata_id}",  # Path endpoint hapus embedding by metadata_id
    )  # Menutup proxy delete vector


# @router.post("/features/extract")  # Endpoint gateway untuk ekstraksi fitur
# async def extract_features(  # Handler request ekstraksi fitur
#     request: Request,  # Request asli dari client
#     file: UploadFile = File(...),  # File gambar wajib dikirim dengan field bernama file
# ):  # Menutup parameter extract_features
#     # Direct proxy for generating CLIP and CNN embeddings.
#     return await proxy_multipart_request(  # Forward multipart ke feature service
#         request,  # Request asli dari client
#         "feature-extraction-service",  # Nama upstream service tujuan
#         "/extract",  # Path endpoint feature service
#         "file",  # Nama field file sesuai kontrak feature service
#         file,  # File gambar dari client
#     )  # Menutup proxy multipart feature extraction


# @router.post("/web-search/search")  # Endpoint gateway untuk web search
# async def search_web(  # Handler request web search
#     request: Request,  # Request asli dari client
#     image: UploadFile = File(...),  # File gambar wajib dikirim dengan field bernama image
# ):  # Menutup parameter search_web
#     # Direct proxy for external reverse image search.
#     return await proxy_multipart_request(  # Forward multipart ke web-search-service
#         request,  # Request asli dari client
#         "web-search-service",  # Nama upstream service tujuan
#         "/search",  # Path endpoint web-search-service
#         "image",  # Nama field file sesuai kontrak web-search-service
#         image,  # File gambar dari client
#     )  # Menutup proxy multipart web search


# @router.api_route("/similarity", methods=["POST"])  # Endpoint gateway untuk similarity check
# async def similarity(request: Request):  # Handler request similarity
#     # Direct proxy for internal and external similarity scoring.
#     return await proxy_request(request, "similarity-check-service", "/similarity")  # Forward ke similarity service


# @router.api_route("/decision", methods=["POST"])  # Endpoint gateway untuk decision engine
# async def decision(request: Request):  # Handler request decision
#     # Direct proxy for risk-level decision calculation.
#     return await proxy_request(request, "decision-engine", "/decision")  # Forward ke decision-engine
