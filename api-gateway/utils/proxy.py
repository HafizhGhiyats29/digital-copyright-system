import httpx  # Import HTTP client async dan exception
from fastapi import HTTPException, Request, Response, UploadFile, status  # Import komponen FastAPI untuk proxy

from config.settings import settings  # Import registry service dari config
from middleware.request_id import REQUEST_ID_HEADER  # Import nama header request id
from utils.request_handler import filter_proxy_headers  # Import helper filter header


def build_target_url(service_name: str, path: str) -> str:  # Membentuk URL upstream service
    service = settings.services.get(service_name)  # Ambil service config berdasarkan nama

    if service is None:  # Validasi service harus terdaftar
        raise HTTPException(  # Lempar error gateway jika service tidak dikenal
            status_code=status.HTTP_502_BAD_GATEWAY,  # Status 502 untuk masalah upstream/gateway
            detail=f"Unknown upstream service: {service_name}",  # Pesan error untuk client
        )  # Menutup HTTPException

    clean_path = path if path.startswith("/") else f"/{path}"  # Pastikan path selalu diawali slash
    return f"{service.base_url}{clean_path}"  # Gabungkan base URL service dan path endpoint


async def proxy_request(request: Request, service_name: str, path: str) -> Response:  # Forward request umum ke upstream
    client: httpx.AsyncClient = request.app.state.http_client  # Ambil HTTP client reusable dari app state
    target_url = build_target_url(service_name, path)  # Buat URL tujuan upstream
    body = await request.body()  # Baca body request asli dari client
    headers = filter_proxy_headers(request.headers)  # Filter header request sebelum diteruskan
    headers[REQUEST_ID_HEADER] = request.state.request_id  # Teruskan request id ke upstream service

    try:  # Mulai proses request ke upstream service
        upstream_response = await client.request(  # Kirim request ke upstream service
            method=request.method,  # Gunakan method HTTP asli dari client
            url=target_url,  # URL service tujuan
            params=request.query_params,  # Teruskan query parameter asli
            content=body,  # Teruskan body request asli
            headers=headers,  # Teruskan header yang sudah difilter
        )  # Menutup request upstream
    except httpx.ConnectError:  # Tangkap error ketika service tidak bisa dihubungi
        raise HTTPException(  # Lempar response service unavailable
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,  # Status 503 untuk service unavailable
            detail=f"{service_name} is unavailable",  # Pesan service tidak tersedia
        ) from None  # Hilangkan traceback internal dari response
    except httpx.TimeoutException:  # Tangkap error timeout ke upstream service
        raise HTTPException(  # Lempar response gateway timeout
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,  # Status 504 untuk timeout
            detail=f"{service_name} timed out",  # Pesan timeout service
        ) from None  # Hilangkan traceback internal dari response
    except httpx.HTTPError as exc:  # Tangkap error HTTP transport lainnya
        raise HTTPException(  # Lempar response bad gateway
            status_code=status.HTTP_502_BAD_GATEWAY,  # Status 502 untuk error gateway
            detail=f"{service_name} gateway error: {exc.__class__.__name__}",  # Pesan ringkas error
        ) from None  # Hilangkan traceback internal dari response

    response_headers = filter_proxy_headers(upstream_response.headers)  # Filter header response upstream

    return Response(  # Buat response gateway berdasarkan response upstream
        content=upstream_response.content,  # Body response dari upstream
        status_code=upstream_response.status_code,  # Status code asli upstream
        headers=response_headers,  # Header response yang aman diteruskan
        media_type=upstream_response.headers.get("content-type"),  # Content-Type dari upstream
    )  # Menutup response gateway


async def proxy_multipart_request(  # Forward request multipart yang dibangun ulang oleh gateway
    request: Request,  # Request asli dari client
    service_name: str,  # Nama upstream service tujuan
    path: str,  # Path endpoint upstream service
    file_field_name: str,  # Nama field file yang diharapkan upstream
    file: UploadFile,  # File upload dari client
    form_data: dict[str, str | float | None] | None = None,  # Field form tambahan
) -> Response:  # Return response dari upstream service
    client: httpx.AsyncClient = request.app.state.http_client  # Ambil HTTP client reusable dari app state
    target_url = build_target_url(service_name, path)  # Buat URL tujuan upstream
    headers = filter_proxy_headers(request.headers)  # Filter header request sebelum diteruskan
    headers.pop("content-type", None)  # Hapus content-type agar httpx membuat boundary multipart baru
    headers[REQUEST_ID_HEADER] = request.state.request_id  # Teruskan request id ke upstream service
    file_bytes = await file.read()  # Baca file upload menjadi bytes
    data = {  # Siapkan form data tambahan
        key: str(value)  # Ubah value menjadi string form field
        for key, value in (form_data or {}).items()  # Loop semua field form tambahan
        if value is not None  # Abaikan field yang tidak diisi
    }  # Menutup form data tambahan
    files = {  # Siapkan payload file multipart
        file_field_name: (  # Nama field file sesuai kontrak upstream
            file.filename or "upload.bin",  # Nama file asli atau fallback
            file_bytes,  # Isi file dalam bytes
            file.content_type or "application/octet-stream",  # Content type file
        )  # Menutup tuple file multipart
    }  # Menutup files payload

    try:  # Mulai proses request multipart ke upstream service
        upstream_response = await client.post(  # Kirim POST multipart ke upstream
            target_url,  # URL service tujuan
            data=data,  # Field form tambahan
            files=files,  # Field file multipart
            headers=headers,  # Header request yang aman diteruskan
        )  # Menutup request upstream
    except httpx.ConnectError:  # Tangkap error ketika service tidak bisa dihubungi
        raise HTTPException(  # Lempar response service unavailable
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,  # Status 503 untuk service unavailable
            detail=f"{service_name} is unavailable",  # Pesan service tidak tersedia
        ) from None  # Hilangkan traceback internal dari response
    except httpx.TimeoutException:  # Tangkap error timeout ke upstream service
        raise HTTPException(  # Lempar response gateway timeout
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,  # Status 504 untuk timeout
            detail=f"{service_name} timed out",  # Pesan timeout service
        ) from None  # Hilangkan traceback internal dari response
    except httpx.HTTPError as exc:  # Tangkap error HTTP transport lainnya
        raise HTTPException(  # Lempar response bad gateway
            status_code=status.HTTP_502_BAD_GATEWAY,  # Status 502 untuk error gateway
            detail=f"{service_name} gateway error: {exc.__class__.__name__}",  # Pesan ringkas error
        ) from None  # Hilangkan traceback internal dari response

    response_headers = filter_proxy_headers(upstream_response.headers)  # Filter header response upstream

    return Response(  # Buat response gateway berdasarkan response upstream
        content=upstream_response.content,  # Body response dari upstream
        status_code=upstream_response.status_code,  # Status code asli upstream
        headers=response_headers,  # Header response yang aman diteruskan
        media_type=upstream_response.headers.get("content-type"),  # Content-Type dari upstream
    )  # Menutup response gateway
