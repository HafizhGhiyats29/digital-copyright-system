import yaml  # Library untuk membaca file YAML
from pathlib import Path  # Library untuk mengatur path file


BASE_DIR = Path(__file__).resolve().parent  # Path folder config
SETTINGS_PATH = BASE_DIR / "settings.yaml"  # Path file settings.yaml


with open(SETTINGS_PATH, "r") as file:  # Membuka file YAML
    settings = yaml.safe_load(file)  # Mengubah YAML menjadi dictionary