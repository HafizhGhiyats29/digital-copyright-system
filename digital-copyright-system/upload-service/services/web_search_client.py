import httpx  # HTTP client
from config.settings import WEB_SEARCH_SERVICE_URL

async def send_to_web_search(file_bytes):

    timeout = httpx.Timeout(60.0)  # ⬅️ solusi cepat & aman

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:  # pakai timeout
            files = {
                "image": ("image.jpg", file_bytes, "image/jpeg")
            }

            response = await client.post(
                WEB_SEARCH_SERVICE_URL,
                files=files
            )

            return response.json()

    except httpx.ConnectError:
        return {"error": "Web Search Service tidak tersedia"}

    except httpx.ReadTimeout:
        return {"error": "Web Search timeout"}