import os  # Import os untuk membaca environment variable
from dataclasses import dataclass  # Import dataclass untuk membuat config object sederhana
from pathlib import Path  # Import Path untuk mengelola path file
from typing import Any  # Import Any untuk tipe data fleksibel

import yaml  # Import PyYAML untuk membaca file settings.yaml


BASE_DIR = Path(__file__).resolve().parent  # Folder tempat file settings.py berada
SETTINGS_PATH = BASE_DIR / "settings.yaml"  # Lokasi file konfigurasi YAML


def _load_yaml(path: Path) -> dict[str, Any]:  # Membaca file YAML menjadi dictionary
    # Keep startup resilient when the YAML file is missing or empty.
    if not path.exists():  # Cek apakah file YAML tidak ada
        return {}  # Return config kosong agar aplikasi tetap bisa startup

    with path.open("r", encoding="utf-8") as file:  # Membuka file YAML dengan encoding UTF-8
        return yaml.safe_load(file) or {}  # Parse YAML dan fallback ke dict kosong jika file kosong


def _get_env(name: str, default: Any) -> Any:  # Mengambil nilai dari environment variable
    # Environment variables override YAML values for Docker/cloud deployments.
    return os.getenv(name, default)  # Return env value jika ada, kalau tidak pakai default


@dataclass(frozen=True)  # Membuat object config immutable
class ServiceConfig:  # Config untuk satu upstream service
    # Upstream service metadata used by health checks and proxy routing.
    name: str  # Nama service, misalnya upload-service
    base_url: str  # Base URL service, misalnya http://localhost:8000
    health_path: str = "/health"  # Path health endpoint service

    @property  # Menjadikan method ini bisa dipanggil seperti attribute
    def health_url(self) -> str:  # Membentuk URL health lengkap
        return f"{self.base_url.rstrip('/')}{self.health_path}"  # Gabungkan base URL dan health path


@dataclass(frozen=True)  # Membuat settings utama immutable
class Settings:  # Config utama API Gateway
    app_name: str  # Nama aplikasi gateway
    app_version: str  # Versi aplikasi gateway
    api_prefix: str  # Prefix API publik, misalnya /api/v1
    request_timeout_seconds: float  # Timeout request ke upstream service
    cors_allow_origins: list[str]  # Daftar origin yang diizinkan CORS
    services: dict[str, ServiceConfig]  # Registry semua upstream service


def load_settings() -> Settings:  # Membaca dan membentuk object settings utama
    # Load static YAML first, then let environment variables override it.
    raw = _load_yaml(SETTINGS_PATH)  # Membaca config dari settings.yaml
    raw_services = raw.get("services", {})  # Mengambil daftar service dari YAML

    # Convert service entries into immutable typed config objects.
    services = {  # Membuat dictionary service config
        name: ServiceConfig(  # Membuat config untuk satu service
            name=name,  # Mengisi nama service
            base_url=str(  # Mengubah base_url menjadi string
                _get_env(  # Environment variable bisa override base_url
                    f"{name.upper().replace('-', '_')}_URL",  # Nama env, contoh UPLOAD_SERVICE_URL
                    service.get("base_url"),  # Default base_url dari YAML
                )  # Menutup pemanggilan _get_env
            ).rstrip("/"),  # Menghapus slash di akhir URL agar konsisten
            health_path=service.get("health_path", "/health"),  # Mengambil health path atau default /health
        )  # Menutup ServiceConfig
        for name, service in raw_services.items()  # Loop semua service dari YAML
    }  # Menutup dictionary services

    # Expose one settings object for the whole gateway.
    return Settings(  # Mengembalikan object Settings final
        app_name=_get_env("APP_NAME", raw.get("app_name", "API Gateway")),  # Nama app dari env/YAML/default
        app_version=_get_env("APP_VERSION", raw.get("app_version", "1.0.0")),  # Versi app dari env/YAML/default
        api_prefix=_get_env("API_PREFIX", raw.get("api_prefix", "/api/v1")),  # Prefix API dari env/YAML/default
        request_timeout_seconds=float(  # Mengubah timeout menjadi float
            _get_env("REQUEST_TIMEOUT_SECONDS", raw.get("request_timeout_seconds", 60))  # Timeout dari env/YAML/default
        ),  # Menutup konversi timeout
        cors_allow_origins=str(  # Mengubah CORS origins menjadi string
            _get_env("CORS_ALLOW_ORIGINS", ",".join(raw.get("cors_allow_origins", ["*"])))  # Origins env/YAML/default
        ).split(","),  # Memecah string origins menjadi list
        services=services,  # Menyimpan registry upstream service
    )  # Menutup object Settings


settings = load_settings()  # Settings global yang digunakan seluruh gateway
