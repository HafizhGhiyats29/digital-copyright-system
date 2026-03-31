import httpx
from config.settings import WEB_SEARCH_SERVICE_URL, REQUEST_TIMEOUT


async def send_to_web_search(file_bytes):

    try:
        async with httpx.AsyncClient() as client:

            files = {
                "image": ("image.jpg", file_bytes, "image/jpeg")
            }

            response = await client.post(
                WEB_SEARCH_SERVICE_URL,
                files=files,
                timeout=REQUEST_TIMEOUT
            )

            return response.json()

    except httpx.ConnectError:
        return {
            "error": "Web Search Service tidak tersedia"
        }