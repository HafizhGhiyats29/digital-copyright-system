from services.clip_service import extract_clip_embedding  # Import extractor CLIP
from services.cnn_service import extract_cnn_embedding  # Import extractor CNN
from utils.image_utils import load_image_from_bytes  # Import loader gambar
from utils.logger import logger  # Import logger


async def extract_features(image_bytes):  # Fungsi utama untuk extract semua fitur gambar
    image = load_image_from_bytes(image_bytes)  # Ubah bytes menjadi PIL Image

    logger.info("Extracting CLIP embedding")  # Log proses CLIP
    clip_embedding = extract_clip_embedding(image)  # Ambil embedding CLIP

    logger.info("Extracting CNN embedding")  # Log proses CNN
    cnn_embedding = extract_cnn_embedding(image)  # Ambil embedding CNN

    return {  # Return hasil akhir
        "status": "processed",  # Status proses
        "clip_embedding": clip_embedding,  # Embedding semantic dari CLIP
        "cnn_embedding": cnn_embedding  # Embedding visual/detail dari CNN
    }  # Menutup dictionary