import os  # Import os untuk membaca environment variable
from dataclasses import dataclass  # Import dataclass untuk membuat config object sederhana
from pathlib import Path  # Import Path untuk mengelola path file
from typing import Any  # Import Any untuk tipe data fleksibel

import yaml  # Import PyYAML untuk membaca file settings.yaml


BASE_DIR = Path(__file__).resolve().parent  # Folder tempat file settings.py berada
PROJECT_ROOT = BASE_DIR.parents[1]  # Root project digital-copyright-system
SETTINGS_PATH = BASE_DIR / "settings.yaml"  # Lokasi file konfigurasi YAML


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.lstrip("\ufeff").strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file(PROJECT_ROOT / ".env")
_load_env_file(BASE_DIR.parent / ".env")


def _load_yaml(path: Path) -> dict[str, Any]:  # Membaca file YAML menjadi dictionary
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _get_env(name: str, default: Any) -> Any:  # Mengambil nilai dari environment variable
    return os.getenv(name, default)


def _get_list_env(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default

    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class ServiceConfig:
    name: str
    base_url: str
    health_path: str = "/health"

    @property
    def health_url(self) -> str:
        return f"{self.base_url.rstrip('/')}{self.health_path}"


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    api_prefix: str
    request_timeout_seconds: float
    cors_allow_origins: list[str]
    services: dict[str, ServiceConfig]
    internal_api_key: str


def load_settings() -> Settings:
    raw = _load_yaml(SETTINGS_PATH)
    raw_services = raw.get("services", {})

    services = {
        name: ServiceConfig(
            name=name,
            base_url=str(
                _get_env(
                    f"{name.upper().replace('-', '_')}_URL",
                    service.get("base_url"),
                )
            ).rstrip("/"),
            health_path=service.get("health_path", "/health"),
        )
        for name, service in raw_services.items()
    }

    return Settings(
        app_name=_get_env("APP_NAME", raw.get("app_name", "API Gateway")),
        app_version=_get_env("APP_VERSION", raw.get("app_version", "1.0.0")),
        api_prefix=_get_env("API_PREFIX", raw.get("api_prefix", "/api/v1")),
        request_timeout_seconds=float(
            _get_env("REQUEST_TIMEOUT_SECONDS", raw.get("request_timeout_seconds", 60))
        ),
        cors_allow_origins=_get_list_env(
            "CORS_ALLOW_ORIGINS",
            raw.get("cors_allow_origins", ["http://localhost:5173", "http://127.0.0.1:5173"]),
        ),
        services=services,
        internal_api_key=str(_get_env("INTERNAL_API_KEY", "")),
    )


settings = load_settings()
