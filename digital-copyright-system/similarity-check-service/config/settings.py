import os  # Library untuk membaca environment variable
import yaml  # Library untuk membaca file YAML
from pathlib import Path  # Library untuk mengatur path file


BASE_DIR = Path(__file__).resolve().parent  # Mengambil lokasi folder config
SETTINGS_PATH = BASE_DIR / "settings.yaml"  # Menentukan lokasi file settings.yaml


with open(SETTINGS_PATH, "r") as file:  # Membuka file settings.yaml
    settings = yaml.safe_load(file) or {}  # Membaca YAML menjadi dictionary Python


def _env(name, default=None):
    return os.getenv(name, default)


settings["milvus_host"] = _env("MILVUS_HOST", settings.get("milvus_host"))
settings["milvus_port"] = _env("MILVUS_PORT", settings.get("milvus_port"))
settings["milvus_collection_name"] = _env(
    "MILVUS_COLLECTION_NAME",
    settings.get("milvus_collection_name"),
)
settings["feature_service_url"] = _env("FEATURE_SERVICE_URL", settings.get("feature_service_url"))
settings["metadata_service_url"] = _env("METADATA_SERVICE_URL", settings.get("metadata_service_url"))
