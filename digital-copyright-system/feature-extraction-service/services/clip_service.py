import torch  # Library PyTorch untuk menjalankan inference model
from models.clipcnn_model import clip_model, clip_processor, device  # Import model CLIP, processor, dan device


def extract_clip_embedding(image):  # Fungsi untuk mengambil embedding CLIP dari gambar PIL
    inputs = clip_processor(  # Preprocess gambar agar sesuai input CLIP
        images=image,  # Gambar PIL yang akan diproses
        return_tensors="pt"  # Output processor dalam bentuk tensor PyTorch
    )  # Menutup processor

    pixel_values = inputs["pixel_values"].to(device)  # Ambil pixel_values lalu pindahkan ke device

    with torch.no_grad():  # Mematikan gradient agar inference lebih ringan
        vision_outputs = clip_model.vision_model(  # Jalankan bagian vision encoder CLIP
            pixel_values=pixel_values  # Input gambar dalam bentuk tensor
        )  # Menutup vision model

        pooled_output = vision_outputs.pooler_output  # Ambil pooled output dari vision model

        image_features = clip_model.visual_projection(  # Proyeksikan pooled output ke embedding CLIP final
            pooled_output  # Input pooled output
        )  # Menutup visual projection

    image_features = image_features / image_features.norm(  # Normalisasi embedding CLIP
        dim=-1,  # Normalisasi pada dimensi terakhir
        keepdim=True  # Pertahankan dimensi agar broadcasting aman
    )  # Menutup normalisasi

    embedding = image_features.squeeze().cpu().tolist()  # Ubah tensor embedding menjadi list Python

    return embedding  # Mengembalikan embedding CLIP