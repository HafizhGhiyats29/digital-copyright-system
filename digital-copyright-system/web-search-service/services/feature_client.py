import httpx  # Library HTTP async
from config.settings import config  # Import konfigurasi
from utils.internal_auth import internal_auth_headers
from utils.logger import logger  # Import logger

FEATURE_SERVICE_URL = config["feature_service_url"]  # URL feature extraction service


async def get_embedding(image_bytes):  # Fungsi untuk meminta embedding ke feature service
    timeout = httpx.Timeout(60.0)  # Timeout request ke feature service

    files = {  # File multipart untuk dikirim ke feature service
        "file": ("candidate.jpg", image_bytes, "image/jpeg")  # Field harus sesuai endpoint feature: file
    }  # Menutup dictionary files

    async with httpx.AsyncClient(timeout=timeout) as client:  # Membuat HTTP client async
        response = await client.post(  # Request POST ke feature extraction
            FEATURE_SERVICE_URL,  # URL endpoint /extract
            files=files,  # File yang dikirim
            headers=internal_auth_headers()
        )  # Menutup request POST

        response.raise_for_status()  # Lempar error jika status bukan 2xx

        result = response.json()  # Ambil response JSON

        logger.info("Feature embedding received from feature-service")  # Log sukses

        return result  # Return seluruh response: status, clip_embedding, cnn_embedding

