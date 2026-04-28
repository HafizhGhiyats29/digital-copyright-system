import httpx  # Import HTTP client exception/type untuk health check upstream
from fastapi import APIRouter, Request  # Import router dan request FastAPI

from config.settings import settings  # Import konfigurasi gateway


router = APIRouter(tags=["health"])  # Membuat router dengan tag health untuk dokumentasi


@router.get("/health")  # Endpoint root health check gateway
async def health():  # Handler health check gateway
    # Lightweight readiness check for the gateway itself.
    return {  # Response sederhana untuk status gateway
        "status": "ok",  # Status gateway sehat
        "service": "api-gateway",  # Nama service yang menjawab
        "version": settings.app_version,  # Versi gateway dari config
    }  # Menutup response health


@router.get(f"{settings.api_prefix}/health")  # Endpoint health check versi API
async def api_health():  # Handler health check versi API
    # Keep a versioned health endpoint beside the root health endpoint.
    return await health()  # Menggunakan response yang sama dengan root health


@router.get(f"{settings.api_prefix}/services/health")  # Endpoint untuk cek semua upstream service
async def services_health(request: Request):  # Handler agregasi health service
    # Check every registered upstream service through its health endpoint.
    client: httpx.AsyncClient = request.app.state.http_client  # Mengambil HTTP client dari app state
    results = {}  # Menyimpan hasil health check per service

    for service_name, service in settings.services.items():  # Loop semua service yang terdaftar
        try:  # Mulai blok request ke upstream service
            response = await client.get(service.health_url)  # Kirim GET ke health endpoint service
            results[service_name] = {  # Simpan hasil jika service merespons
                "status": "ok" if response.is_success else "error",  # Status ok untuk HTTP 2xx
                "status_code": response.status_code,  # Simpan status code asli dari service
            }  # Menutup hasil service sukses/error
        except httpx.HTTPError as exc:  # Tangkap error koneksi/timeout/transport
            # A failed health request should degrade the gateway, not crash it.
            results[service_name] = {  # Simpan hasil jika service tidak bisa dihubungi
                "status": "unavailable",  # Tandai service tidak tersedia
                "error": exc.__class__.__name__,  # Simpan nama error tanpa stack trace
            }  # Menutup hasil service unavailable

    # Gateway is degraded when one or more upstream services are not healthy.
    overall_status = (  # Hitung status keseluruhan gateway
        "ok"  # Status ok jika semua service sehat
        if all(result["status"] == "ok" for result in results.values())  # Cek semua hasil service
        else "degraded"  # Status degraded jika ada service bermasalah
    )  # Menutup perhitungan status keseluruhan

    return {  # Response agregasi health check
        "status": overall_status,  # Status keseluruhan gateway
        "services": results,  # Detail status setiap upstream service
    }  # Menutup response services health
