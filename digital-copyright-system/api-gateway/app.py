from contextlib import asynccontextmanager  # Import helper untuk lifecycle startup/shutdown FastAPI

import httpx  # Import HTTP client async untuk request ke service lain
from fastapi import FastAPI  # Import class utama FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Import middleware CORS

from config.settings import settings  # Import konfigurasi gateway
from middleware.request_id import RequestIdMiddleware  # Import middleware request id
from router.health_routes import router as health_router  # Import router health check
from router.proxy_routes import router as proxy_router  # Import router proxy endpoint


@asynccontextmanager  # Menandai function ini sebagai async context manager
async def lifespan(app: FastAPI):  # Lifecycle yang berjalan saat aplikasi start dan shutdown
    # Reuse one async HTTP client for all proxied requests during app lifetime.
    timeout = httpx.Timeout(settings.request_timeout_seconds)  # Membuat konfigurasi timeout HTTP client
    app.state.http_client = httpx.AsyncClient(timeout=timeout)  # Menyimpan HTTP client reusable di state app
    yield  # Memberikan kontrol ke aplikasi selama server berjalan
    await app.state.http_client.aclose()  # Menutup HTTP client saat aplikasi shutdown


def create_app() -> FastAPI:  # Factory function untuk membuat instance FastAPI
    # Build the FastAPI instance from centralized settings.
    app = FastAPI(  # Membuat aplikasi FastAPI
        title=settings.app_name,  # Nama aplikasi dari config
        version=settings.app_version,  # Versi aplikasi dari config
        description="API Gateway for the Digital Copyright System",  # Deskripsi aplikasi untuk docs
        lifespan=lifespan,  # Memasang lifecycle startup/shutdown
    )  # Menutup konfigurasi FastAPI

    # Add cross-cutting middleware before registering route handlers.
    app.state.settings = settings  # Simpan settings agar router manual bisa memakai internal API key
    app.add_middleware(RequestIdMiddleware)  # Menambahkan request id untuk tracing request
    app.add_middleware(  # Menambahkan middleware CORS
        CORSMiddleware,  # Class middleware CORS dari FastAPI/Starlette
        allow_origins=settings.cors_allow_origins,  # Origin frontend yang diizinkan
        allow_credentials=True,  # Mengizinkan credentials seperti cookie/header auth
        allow_methods=["*"],  # Mengizinkan semua method HTTP
        allow_headers=["*"],  # Mengizinkan semua request header
    )  # Menutup konfigurasi middleware CORS

    # Public gateway endpoints are mounted under the configured API prefix.
    app.include_router(health_router)  # Mendaftarkan endpoint health check
    app.include_router(proxy_router, prefix=settings.api_prefix)  # Mendaftarkan endpoint proxy dengan prefix API

    return app  # Mengembalikan instance aplikasi FastAPI


app = create_app()  # Instance aplikasi yang dibaca oleh uvicorn

