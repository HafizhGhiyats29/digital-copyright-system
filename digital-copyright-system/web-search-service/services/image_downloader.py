import httpx  # HTTP client

async def download_image(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        return response.content  # bytes