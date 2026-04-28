import torch  # tensor
from PIL import Image  # image
import io  # bytes
from models.clip_model import get_model  # model


def extract_embedding(image_bytes):

    model, processor, device = get_model()

    # 1. bytes → image
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # 2. preprocessing
    inputs = processor(images=image, return_tensors="pt").to(device)

    # 3. inference (WAJIB pakai ini saja)
    with torch.no_grad():
        outputs = model.vision_model(
            pixel_values=inputs["pixel_values"]
        )

        image_features = outputs.pooler_output  # ← ini tensor fix

    # 🔥 DEBUG (opsional tapi penting)
    print(type(image_features))  # HARUS torch.Tensor

    # 4. normalisasi
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)

    # 5. ke list
    embedding = image_features.cpu().numpy().flatten().tolist()

    return embedding