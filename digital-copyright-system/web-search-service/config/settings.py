import os
import yaml

# path ke file yaml
config_path = os.path.join(os.path.dirname(__file__), "settings.yaml")

# load yaml
with open(config_path, "r") as f:
    config = yaml.safe_load(f) or {}


def _env(name, default=None):
    return os.getenv(name, default)


config["serpapi_key"] = _env("SERPAPI_KEY", config.get("serpapi_key"))
config["feature_service_url"] = _env("FEATURE_SERVICE_URL", config.get("feature_service_url"))
config["request_timeout"] = int(_env("REQUEST_TIMEOUT", config.get("request_timeout", 20)))

cloudinary_config = config.setdefault("cloudinary", {})
cloudinary_config["cloud_name"] = _env("CLOUDINARY_CLOUD_NAME", cloudinary_config.get("cloud_name"))
cloudinary_config["api_key"] = _env("CLOUDINARY_API_KEY", cloudinary_config.get("api_key"))
cloudinary_config["api_secret"] = _env("CLOUDINARY_API_SECRET", cloudinary_config.get("api_secret"))
