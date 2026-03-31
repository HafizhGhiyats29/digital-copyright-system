import httpx
from config.settings import config

SERPAPI_KEY = config["serpapi_key"]


async def search_image():

    params = {
        "engine": "google_lens",
        "url": "https://drive.google.com/uc?export=view&id=1uR9gIO0u0aIjQxinmt3z7N6f4LL0AdMX",
        "api_key": SERPAPI_KEY
    }

    async with httpx.AsyncClient(timeout=60) as client:

        response = await client.get(
            "https://serpapi.com/search",
            params=params
        )

        return response.json()