import httpx

from config.settings import WEB_SEARCH_SERVICE_URL
from utils.internal_auth import internal_auth_headers


async def send_to_web_search(file_bytes):
    timeout = httpx.Timeout(60.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            files = {
                "image": ("image.jpg", file_bytes, "image/jpeg"),
            }
            response = await client.post(
                WEB_SEARCH_SERVICE_URL,
                files=files,
                headers=internal_auth_headers(),
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        return {"found_on_web": False, "matches": [], "error": "Web Search Service tidak tersedia"}

    except httpx.ReadTimeout:
        return {"found_on_web": False, "matches": [], "error": "Web Search timeout"}

    except httpx.HTTPStatusError as exc:
        return {"found_on_web": False, "matches": [], "error": f"Web Search HTTP error: {exc}"}
