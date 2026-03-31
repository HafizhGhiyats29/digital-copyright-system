import yaml
import os

# path ke file yaml
config_path = os.path.join(os.path.dirname(__file__), "settings.yaml")

# load yaml
with open(config_path, "r") as f:
    config = yaml.safe_load(f)