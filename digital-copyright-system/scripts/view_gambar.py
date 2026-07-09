from pathlib import Path
import sys
from PIL import Image, ImageDraw, ExifTags

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEATURE_SERVICE_DIR = PROJECT_ROOT / "feature-extraction-service"
sys.path.insert(0, str(FEATURE_SERVICE_DIR))

from utils.image_utils import load_image_from_bytes, letterbox_image

input_path = PROJECT_ROOT / "evaluation_dataset" / "modified" / "Afternoon-with-Lily_rotate.png"
output_path = PROJECT_ROOT / "reports" / "letterbox_comparison.png"

raw = Image.open(input_path)

orientation_key = None
for key, value in ExifTags.TAGS.items():
    if value == "Orientation":
        orientation_key = key
        break

exif = raw.getexif()
print("EXIF Orientation:", exif.get(orientation_key))

original = load_image_from_bytes(input_path.read_bytes())
letterboxed = letterbox_image(original)

preview_original = original.copy()
preview_original.thumbnail((224, 224))

canvas = Image.new("RGB", (500, 280), "white")
draw = ImageDraw.Draw(canvas)

canvas.paste(preview_original, (20, 40))
canvas.paste(letterboxed, (260, 40))

draw.text((20, 15), f"Original {original.size}", fill="black")
draw.text((260, 15), f"Letterbox {letterboxed.size}", fill="black")

output_path.parent.mkdir(parents=True, exist_ok=True)
canvas.save(output_path)

print(f"Saved: {output_path}")