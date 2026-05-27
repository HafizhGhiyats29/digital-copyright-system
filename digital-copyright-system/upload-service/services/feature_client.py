import httpx

from config.settings import config
from utils.internal_auth import internal_auth_headers


FEATURE_SERVICE_URL = config["feature_service_url"]


async def get_embedding(image_bytes):
    timeout = httpx.Timeout(60.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        files = {
            "file": ("image.jpg", image_bytes, "image/jpeg"),
        }
        response = await client.post(
            FEATURE_SERVICE_URL,
            files=files,
            headers=internal_auth_headers(),
        )
        response.raise_for_status()
        return response.json()
