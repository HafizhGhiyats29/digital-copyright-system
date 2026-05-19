import os  # Library untuk membaca environment variable
import yaml  # Library untuk membaca file YAML
from pathlib import Path  # Library untuk mengatur path file


BASE_DIR = Path(__file__).resolve().parent  # Path folder config
SETTINGS_PATH = BASE_DIR / "settings.yaml"  # Path file settings.yaml


with open(SETTINGS_PATH, "r") as file:  # Membuka file YAML
    settings = yaml.safe_load(file) or {}  # Mengubah YAML menjadi dictionary


settings["device"] = os.getenv("MODEL_DEVICE", settings.get("device", "cpu"))
settings["clip_model_name"] = os.getenv("CLIP_MODEL_NAME", settings.get("clip_model_name"))
settings["image_size"] = int(os.getenv("IMAGE_SIZE", settings.get("image_size", 224)))
