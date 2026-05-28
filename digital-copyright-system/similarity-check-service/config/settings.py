import os
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = BASE_DIR / "settings.yaml"

with SETTINGS_PATH.open("r", encoding="utf-8") as file:
    settings = yaml.safe_load(file) or {}

settings["milvus_host"] = os.getenv("MILVUS_HOST", settings.get("milvus_host", "localhost"))
settings["milvus_port"] = os.getenv("MILVUS_PORT", settings.get("milvus_port", "19530"))
settings["milvus_collection_name"] = os.getenv("MILVUS_COLLECTION_NAME", settings.get("milvus_collection_name", "copyright_embeddings"))
settings["metadata_service_url"] = os.getenv("METADATA_SERVICE_URL", settings.get("metadata_service_url", "http://localhost:8006/metadata"))
settings["feature_service_url"] = os.getenv("FEATURE_SERVICE_URL", settings.get("feature_service_url", "http://localhost:8002/extract"))
settings["top_k_internal"] = int(os.getenv("TOP_K_INTERNAL", settings.get("top_k_internal", 3)))
settings["top_k_external"] = int(os.getenv("TOP_K_EXTERNAL", settings.get("top_k_external", 3)))
settings["clip_weight"] = float(os.getenv("CLIP_WEIGHT", settings.get("clip_weight", 0.4)))
settings["cnn_weight"] = float(os.getenv("CNN_WEIGHT", settings.get("cnn_weight", 0.6)))
