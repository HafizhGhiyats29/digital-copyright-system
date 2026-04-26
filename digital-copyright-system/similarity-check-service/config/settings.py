import yaml  # Library untuk membaca file YAML
from pathlib import Path  # Library untuk mengatur path file


BASE_DIR = Path(__file__).resolve().parent  # Mengambil lokasi folder config
SETTINGS_PATH = BASE_DIR / "settings.yaml"  # Menentukan lokasi file settings.yaml


with open(SETTINGS_PATH, "r") as file:  # Membuka file settings.yaml
    settings = yaml.safe_load(file)  # Membaca YAML menjadi dictionary Python