import os
import yaml

# path ke yaml
config_path = os.path.join(os.path.dirname(__file__), "settings.yaml")

# load yaml
with open(config_path, "r") as f:
    config = yaml.safe_load(f) or {}


def _env(name, default=None):
    return os.getenv(name, default)


config["feature_service_url"] = _env("FEATURE_SERVICE_URL", config.get("feature_service_url"))
config["web_search_service_url"] = _env("WEB_SEARCH_SERVICE_URL", config.get("web_search_service_url"))
config["similarity_service_url"] = _env("SIMILARITY_SERVICE_URL", config.get("similarity_service_url"))
config["decision_service_url"] = _env("DECISION_SERVICE_URL", config.get("decision_service_url"))
config["metadata_service_url"] = _env("METADATA_SERVICE_URL", config.get("metadata_service_url"))
config["embedding_service_url"] = _env("EMBEDDING_SERVICE_URL", config.get("embedding_service_url"))
config["request_timeout"] = int(_env("REQUEST_TIMEOUT", config.get("request_timeout", 20)))
config["max_file_size"] = int(_env("MAX_FILE_SIZE", config.get("max_file_size", 5242880)))

cloudinary_config = config.setdefault("cloudinary", {})
cloudinary_config["cloud_name"] = _env("CLOUDINARY_CLOUD_NAME", cloudinary_config.get("cloud_name"))
cloudinary_config["api_key"] = _env("CLOUDINARY_API_KEY", cloudinary_config.get("api_key"))
cloudinary_config["api_secret"] = _env("CLOUDINARY_API_SECRET", cloudinary_config.get("api_secret"))
cloudinary_config["folder"] = _env("CLOUDINARY_FOLDER", cloudinary_config.get("folder", "copyright-registrations"))


# 🔥 mapping ke variable lama (BACKWARD COMPATIBLE)
WEB_SEARCH_SERVICE_URL = config.get("web_search_service_url")
MAX_FILE_SIZE = config.get("max_file_size")
REQUEST_TIMEOUT = config.get("request_timeout")
FEATURE_SERVICE_URL = config.get("feature_service_url")
