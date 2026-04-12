import yaml
import os

# path ke yaml
config_path = os.path.join(os.path.dirname(__file__), "settings.yaml")

# load yaml
with open(config_path, "r") as f:
    config = yaml.safe_load(f)


# 🔥 mapping ke variable lama (BACKWARD COMPATIBLE)
WEB_SEARCH_SERVICE_URL = config.get("web_search_service_url")
MAX_FILE_SIZE = config.get("max_file_size")
REQUEST_TIMEOUT = config.get("request_timeout")
FEATURE_SERVICE_URL = config.get("feature_service_url")