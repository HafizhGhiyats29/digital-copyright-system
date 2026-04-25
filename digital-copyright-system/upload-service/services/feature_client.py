import httpx  # Import HTTP client async
from config.settings import config  # Import config


FEATURE_SERVICE_URL = config["feature_service_url"]  # Ambil URL feature-service dari config


async def get_embedding(image_bytes):  # Fungsi untuk mengambil CLIP + CNN embedding
    timeout = httpx.Timeout(60.0)  # Timeout request ke feature-service

    async with httpx.AsyncClient(timeout=timeout) as client:  # Membuat HTTP client dengan timeout
        files = {  # Membuat file multipart
            "file": ("image.jpg", image_bytes, "image/jpeg")  # Field harus "file" sesuai feature_router.py
        }  # Menutup dictionary files

        response = await client.post(  # Mengirim request POST ke feature-service
            FEATURE_SERVICE_URL,  # URL endpoint /extract
            files=files  # File gambar yang dikirim
        )  # Menutup request

        response.raise_for_status()  # Lempar error jika response bukan 2xx

        return response.json()  # Return seluruh JSON: status, clip_embedding, cnn_embedding