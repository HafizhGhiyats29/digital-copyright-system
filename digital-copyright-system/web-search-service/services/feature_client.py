import httpx  # HTTP client
from config.settings import config  # ambil config

FEATURE_SERVICE_URL = config["feature_service_url"]

async def get_embedding(image_bytes):

    async with httpx.AsyncClient() as client:

        files = {
            "image": ("image.jpg", image_bytes, "image/jpeg")
        }

        response = await client.post(
            FEATURE_SERVICE_URL,
            files=files
        )

        return response.json()["embedding"]