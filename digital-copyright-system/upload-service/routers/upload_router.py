from copy import deepcopy
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends  # Import FastAPI tools
from typing import Optional  # Import Optional untuk parameter opsional
from pydantic import BaseModel, Field  # Schema untuk registrasi metadata setelah pengecekan
from utils.image_validator import validate_image
from utils.internal_auth import require_internal_api_key  # Import validator gambar
from services.web_search_client import send_to_web_search  # Import client web-search
from schemas.response_schema import UploadResponse  # Import schema response
from utils.logger import logger  # Import logger
from config.settings import MAX_FILE_SIZE  # Import batas ukuran file
from services.feature_client import get_embedding  # Import client feature-service
from services.similarity_client import send_to_similarity  # Import client similarity-service
from services.decision_client import send_to_decision  # Import client decision-engine
from services.metadata_client import create_metadata, update_embedding_reference  # Client metadata service
from services.cloudinary_client import delete_image, upload_image as upload_image_to_cloudinary  # Client Cloudinary untuk simpan gambar karya
from services.embedding_client import DEFAULT_EMBEDDING_VERSION, insert_embedding  # Client similarity-service untuk simpan embedding Milvus
from services.temporary_embedding_store import delete_temporary_embedding, get_temporary_embedding, review_temporary_embedding, save_temporary_embedding  # Simpan embedding sementara untuk registrasi
import re  # Import regex untuk membuat public_id Cloudinary aman
import uuid  # Import uuid untuk request id


router = APIRouter()  # Membuat router FastAPI

ALLOWED_UPLOAD_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}  # MIME type gambar yang diterima


class RegisterMetadataRequest(BaseModel):  # Request registrasi metadata setelah upload/check aman
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


class ReviewCheckRequest(BaseModel):  # Request keputusan review manual untuk check_id
    reason: Optional[str] = Field(default=None, description="Catatan/alasan reviewer")


class DeleteCloudinaryRequest(BaseModel):  # Request hapus gambar Cloudinary dari gateway/orchestrator
    public_id: str = Field(..., min_length=1, description="Cloudinary public_id gambar yang akan dihapus")


def build_cloudinary_public_id(title: str, identifier: Optional[str]) -> str:  # Membuat nama file Cloudinary yang readable dan unik
    title_slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    identifier_slug = re.sub(r"[^a-zA-Z0-9]+", "-", (identifier or "").strip()).strip("-")

    if title_slug and identifier_slug:
        return f"{title_slug}-{identifier_slug}"

    return title_slug or identifier_slug or str(uuid.uuid4())


def build_registration_gate(decision_result):  # Menentukan apakah hasil cek boleh lanjut registrasi
    decision = decision_result.get("decision", {}) if decision_result else {}  # Ambil detail keputusan
    status = decision.get("status", "unknown")  # Ambil status decision
    requires_review = bool(decision.get("requires_review", True))  # Default aman: perlu review

    if status == "high_similarity":  # Indikasi kuat plagiarisme
        return {
            "can_register": False,
            "registration_status": "blocked",
            "registration_reason": "Registrasi ditolak karena gambar terindikasi memiliki kemiripan tinggi.",
        }

    if requires_review:  # Kasus sedang/possible perlu review manual
        return {
            "can_register": False,
            "registration_status": "review_required",
            "registration_reason": "Registrasi ditahan karena hasil pengecekan masih membutuhkan review manual.",
        }

    return {
        "can_register": True,
        "registration_status": "allowed",
        "registration_reason": "Registrasi diizinkan karena tidak ada indikasi plagiarisme yang perlu ditinjau.",
    }


@router.post("/register-metadata", dependencies=[Depends(require_internal_api_key)])  # Endpoint registrasi metadata yang wajib melewati hasil cek plagiarisme
async def register_metadata(data: RegisterMetadataRequest):
    temporary_check = get_temporary_embedding(data.check_id)  # Ambil hasil embedding/decision sementara

    if temporary_check is None:  # Jika check_id tidak ditemukan atau expired
        raise HTTPException(status_code=404, detail="Check ID tidak ditemukan atau sudah kedaluwarsa")

    if not temporary_check["can_register"]:  # Jika hasil cek tidak aman
        decision = temporary_check.get("decision", {})  # Ambil detail decision untuk response
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Metadata tidak dapat ditambahkan karena hasil pengecekan belum aman untuk registrasi",
                "decision_result": decision,
            },
        )

    metadata_payload = data.model_dump(exclude_none=True)  # Simpan check_id dan abaikan field optional kosong
    report_snapshot = deepcopy(temporary_check.get("report"))

    if report_snapshot:
        report_saved_at = datetime.now(timezone.utc).isoformat()
        report_snapshot["saved_at"] = report_saved_at
        metadata_payload["report"] = report_snapshot
        metadata_payload["report_saved_at"] = report_saved_at
    cloudinary_public_id = None  # Dipakai untuk rollback jika create metadata gagal

    if not metadata_payload.get("image_url") and temporary_check.get("file_bytes") is not None:
        try:
            upload_result = await upload_image_to_cloudinary(  # Simpan gambar asli ke Cloudinary saat registrasi
                temporary_check["file_bytes"],
                public_id=build_cloudinary_public_id(data.title, data.ki_uuid or data.ki_id or data.check_id),
            )
            metadata_payload["image_url"] = upload_result.get("image_url")
            metadata_payload["cloudinary_public_id"] = upload_result.get("cloudinary_public_id")
            cloudinary_public_id = metadata_payload["cloudinary_public_id"]
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Gagal menyimpan gambar ke Cloudinary",
                    "error": str(exc),
                },
            ) from exc

    metadata_payload.update({  # Set status embedding awal
        "milvus_collection": None,
        "milvus_id": None,
        "embedding_version": None,
        "embedding_status": "pending",
    })

    try:
        created_metadata = await create_metadata(metadata_payload)  # Buat metadata jika aman
    except Exception as exc:
        if cloudinary_public_id:
            await delete_image(cloudinary_public_id)
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Gagal menyimpan metadata setelah gambar diupload ke Cloudinary",
                "error": str(exc),
            },
        ) from exc
    metadata_id = created_metadata["id"]  # ID metadata dipakai sebagai foreign key di Milvus

    try:
        embedding_result = await insert_embedding(  # Promosikan embedding sementara ke Milvus
            metadata_id=metadata_id,
            feature=temporary_check["feature"],
            embedding_version=DEFAULT_EMBEDDING_VERSION,
        )

        updated_metadata = await update_embedding_reference(  # Simpan referensi vector ke metadata
            metadata_id=metadata_id,
            embedding_reference={
                "milvus_collection": embedding_result.get("milvus_collection"),
                "milvus_id": embedding_result.get("milvus_id"),
                "embedding_version": embedding_result.get("embedding_version", DEFAULT_EMBEDDING_VERSION),
                "embedding_status": "ready",
            },
        )

    except Exception as exc:
        try:
            await update_embedding_reference(  # Tandai gagal agar metadata tidak terlihat siap dicari
                metadata_id=metadata_id,
                embedding_reference={
                    "embedding_version": DEFAULT_EMBEDDING_VERSION,
                    "embedding_status": "failed",
                },
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=502,
            detail={
                "message": "Metadata berhasil dibuat, tetapi embedding gagal disimpan ke Milvus",
                "metadata_id": metadata_id,
                "error": str(exc),
            },
        ) from exc

    delete_temporary_embedding(data.check_id)  # Hapus embedding sementara setelah berhasil dipromosikan

    return {
        "status": "registered",
        "check_id": data.check_id,
        "metadata": updated_metadata,
        "embedding": embedding_result,
        "embedding_status": "ready",
        "message": "Metadata berhasil ditambahkan dan embedding sudah tersimpan di Milvus.",
    }


@router.post("/review-check/{check_id}/approve", dependencies=[Depends(require_internal_api_key)])  # Endpoint approval manual untuk hasil cek yang butuh review
async def approve_check(check_id: str, data: ReviewCheckRequest | None = None):
    reviewed = review_temporary_embedding(
        check_id=check_id,
        approved=True,
        reason=data.reason if data else None,
    )

    if reviewed is None:
        raise HTTPException(status_code=404, detail="Check ID tidak ditemukan atau sudah kedaluwarsa")

    return {
        "check_id": check_id,
        "can_register": True,
        "manual_review_status": "approved",
        "manual_review_reason": reviewed.get("manual_review_reason"),
        "message": "Hasil cek disetujui reviewer. Metadata dapat didaftarkan menggunakan check_id ini.",
    }


@router.post("/review-check/{check_id}/reject", dependencies=[Depends(require_internal_api_key)])  # Endpoint penolakan manual untuk hasil cek
async def reject_check(check_id: str, data: ReviewCheckRequest | None = None):
    reviewed = review_temporary_embedding(
        check_id=check_id,
        approved=False,
        reason=data.reason if data else None,
    )

    if reviewed is None:
        raise HTTPException(status_code=404, detail="Check ID tidak ditemukan atau sudah kedaluwarsa")

    return {
        "check_id": check_id,
        "can_register": False,
        "manual_review_status": "rejected",
        "manual_review_reason": reviewed.get("manual_review_reason"),
        "message": "Hasil cek ditolak reviewer. Metadata tidak dapat didaftarkan.",
    }


@router.post("/cloudinary/delete", dependencies=[Depends(require_internal_api_key)])  # Endpoint internal untuk hapus gambar Cloudinary saat metadata dihapus
async def delete_cloudinary_image(data: DeleteCloudinaryRequest):
    try:
        result = await delete_image(data.public_id)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Gagal menghapus gambar Cloudinary",
                "public_id": data.public_id,
                "error": str(exc),
            },
        ) from exc

    return {
        "public_id": data.public_id,
        "cloudinary_result": result,
    }


@router.post("/upload", response_model=UploadResponse)  # Endpoint upload gambar
async def upload_image(  # Fungsi menerima upload gambar dan threshold
    file: UploadFile = File(...),  # File gambar wajib dikirim
    preset: Optional[str] = Form(None),  # Preset threshold opsional
    high_threshold: Optional[float] = Form(None),  # Custom high threshold opsional
    medium_threshold: Optional[float] = Form(None),  # Custom medium threshold opsional
    low_threshold: Optional[float] = Form(None)  # Custom low threshold opsional
):  # Menutup parameter function
    request_id = str(uuid.uuid4())  # Membuat request id unik

    logger.info(f"[{request_id}] Upload request received")  # Log request diterima

    if file.content_type not in ALLOWED_UPLOAD_CONTENT_TYPES:  # Validasi tipe file dari request
        logger.warning(f"[{request_id}] Unsupported file type: {file.content_type}")  # Log tipe file tidak didukung
        raise HTTPException(status_code=400, detail="Format gambar harus JPG, PNG, atau WEBP")  # Return error 400

    file_bytes = await file.read()  # Membaca file menjadi bytes

    logger.info(f"[{request_id}] File name: {file.filename}")  # Log nama file
    logger.info(f"[{request_id}] File size: {len(file_bytes)} bytes")  # Log ukuran file

    if len(file_bytes) > MAX_FILE_SIZE:  # Mengecek ukuran file
        logger.warning(f"[{request_id}] File too large")  # Log file terlalu besar
        raise HTTPException(status_code=400, detail="File terlalu besar")  # Return error 400

    try:
        validate_image(file_bytes)  # Validasi isi gambar
    except ValueError as exc:
        logger.warning(f"[{request_id}] Invalid image content: {exc}")  # Log gambar tidak valid
        raise HTTPException(status_code=400, detail=str(exc)) from exc  # Return error validasi gambar

    logger.info(f"[{request_id}] Image validation passed")  # Log gambar valid

    custom_thresholds = None  # Default tidak memakai custom threshold

    if preset:  # Jika user memilih preset, gunakan preset dan abaikan threshold manual
        logger.info(f"[{request_id}] Using threshold preset: {preset}")  # Log preset yang dipakai

    else:  # Jika preset tidak diisi, baru cek custom threshold
        threshold_values = [high_threshold, medium_threshold, low_threshold]  # Kumpulkan input threshold manual

        if any(value is not None for value in threshold_values):  # Jika salah satu threshold manual diisi
            if not all(value is not None for value in threshold_values):  # Jika tidak lengkap
             raise HTTPException(status_code=400, detail="Custom threshold harus lengkap: high, medium, low")  # Error threshold tidak lengkap

            custom_thresholds = {  # Buat custom threshold
                "high": high_threshold,  # Threshold high
                "medium": medium_threshold,  # Threshold medium
                "low": low_threshold  # Threshold low
            }  # Menutup dictionary custom threshold

            logger.info(f"[{request_id}] Using custom thresholds: {custom_thresholds}")  # Log custom threshold

    original_feature = await get_embedding(file_bytes)  # Ambil CLIP + CNN embedding original

    original_clip_embedding = original_feature["clip_embedding"]  # Ambil CLIP embedding original
    original_cnn_embedding = original_feature["cnn_embedding"]  # Ambil CNN embedding original

    web_result = await send_to_web_search(file_bytes)  # Kirim gambar ke web-search-service

    web_matches = web_result.get("matches", [])  # Ambil kandidat external dari web-search

    similarity_result = await send_to_similarity(  # Kirim data ke similarity-service
        original_clip_embedding,  # CLIP embedding original
        original_cnn_embedding,  # CNN embedding original
        web_matches  # Kandidat external
    )  # Menutup similarity call

    overall_score = similarity_result.get("overall_score", 0.0)  # Ambil overall_score dari similarity-service
    best_match = similarity_result.get("best_match") or {}  # Ambil kandidat terbaik untuk detail score
    clip_score = best_match.get("clip_score")  # Ambil clip_score kandidat terbaik jika ada
    cnn_score = best_match.get("cnn_score")  # Ambil cnn_score kandidat terbaik jika ada

    decision_result = await send_to_decision(  # Kirim overall_score ke decision-engine
        overall_score=overall_score,  # Score utama similarity
        clip_score=clip_score,  # Score CLIP kandidat terbaik
        cnn_score=cnn_score,  # Score CNN kandidat terbaik
        preset=preset,  # Preset dari frontend
        thresholds=custom_thresholds  # Custom threshold dari frontend
    )  # Menutup decision call

    registration_gate = build_registration_gate(decision_result)  # Tentukan izin registrasi
    check_id = request_id  # Gunakan request id sebagai id pengecekan

    report_snapshot = {
        "status": "processed",
        "check_id": check_id,
        "can_register": registration_gate["can_register"],
        "registration_status": registration_gate["registration_status"],
        "registration_reason": registration_gate["registration_reason"],
        "original_feature": {
            "status": original_feature.get("status", "processed"),
        },
        "web_search_result": web_result,
        "similarity_result": similarity_result,
        "decision_result": decision_result,
    }

    save_temporary_embedding(  # Simpan embedding sementara untuk dipakai ulang jika registrasi diizinkan
        check_id=check_id,  # ID pengecekan
        feature=original_feature,  # Embedding hasil feature extraction
        decision=decision_result,  # Keputusan hasil pengecekan
        can_register=registration_gate["can_register"],  # Status izin registrasi
        file_bytes=file_bytes,  # Bytes gambar asli untuk upload Cloudinary saat registrasi
        filename=file.filename,  # Nama file asli untuk audit sederhana
        report=report_snapshot,  # Snapshot hasil pemeriksaan untuk disimpan bersama metadata
    )  # Menutup penyimpanan embedding sementara

    return {  # Mengembalikan response final ke frontend
        "status": "processed",  # Status proses
        "check_id": check_id,  # ID hasil pengecekan untuk registrasi lanjutan
        "can_register": registration_gate["can_register"],  # Apakah boleh registrasi metadata
        "registration_status": registration_gate["registration_status"],  # Status registrasi
        "registration_reason": registration_gate["registration_reason"],  # Alasan keputusan registrasi
        "original_feature": original_feature,  # Embedding original
        "web_search_result": web_result,  # Hasil web search
        "similarity_result": similarity_result,  # Hasil similarity
        "decision_result": decision_result  # Hasil decision-engine
    }  # Menutup response dictionary




