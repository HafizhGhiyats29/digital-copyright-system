import yaml  # Library untuk membaca file YAML
from pathlib import Path  # Library untuk mengatur path file


BASE_DIR = Path(__file__).resolve().parent  # Mengambil path folder config
SETTINGS_PATH = BASE_DIR / "settings.yaml"  # Menentukan path file settings.yaml


with open(SETTINGS_PATH, "r") as file:  # Membuka file settings.yaml
    settings = yaml.safe_load(file)  # Membaca isi YAML menjadi dictionary bernama settings