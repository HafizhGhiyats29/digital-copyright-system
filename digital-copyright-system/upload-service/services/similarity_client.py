import httpx

from config.settings import config
from utils.internal_auth import internal_auth_headers


SIMILARITY_SERVICE_URL = config["similarity_service_url"]


async def send_to_similarity(query_clip_embedding, query_cnn_embedding, web_matches):
    timeout = httpx.Timeout(60.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            SIMILARITY_SERVICE_URL,
            json={
                "clip_embedding": query_clip_embedding,
                "cnn_embedding": query_cnn_embedding,
                "web_matches": web_matches,
            },
            headers=internal_auth_headers(),
        )
        response.raise_for_status()
        return response.json()
