import os
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
CONFIG_PATH = Path(__file__).resolve().parent / "settings.yaml"


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
_load_env_file(BASE_DIR / ".env")

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    config = yaml.safe_load(file) or {}

config["feature_service_url"] = os.getenv("FEATURE_SERVICE_URL", config.get("feature_service_url"))
config["request_timeout"] = int(os.getenv("REQUEST_TIMEOUT", config.get("request_timeout", 20)))

cloudinary_config = config.setdefault("cloudinary", {})
cloudinary_config["cloud_name"] = os.getenv("CLOUDINARY_CLOUD_NAME", cloudinary_config.get("cloud_name"))
cloudinary_config["api_key"] = os.getenv("CLOUDINARY_API_KEY", cloudinary_config.get("api_key"))
cloudinary_config["api_secret"] = os.getenv("CLOUDINARY_API_SECRET", cloudinary_config.get("api_secret"))

config["serpapi_key"] = os.getenv("SERPAPI_KEY", config.get("serpapi_key"))
