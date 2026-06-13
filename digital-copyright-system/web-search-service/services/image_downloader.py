import httpx  # HTTP client

async def download_image(url):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if not content_type.startswith("image/"):
            raise ValueError(f"URL kandidat tidak mengembalikan gambar: {content_type or 'unknown'}")

        return response.content  # bytes
