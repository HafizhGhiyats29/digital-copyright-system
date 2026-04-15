import httpx  # HTTP client
from config.settings import config  # config

SIMILARITY_SERVICE_URL = config["similarity_service_url"]  # ambil URL


async def send_to_similarity(query_embedding, web_matches):

    async with httpx.AsyncClient() as client:  # buat client

        response = await client.post(
            SIMILARITY_SERVICE_URL,  # endpoint similarity
            json={
                "embedding": query_embedding,   # embedding user
                "web_matches": web_matches      # hasil dari web search
            }
        )

        return response.json()  # return hasil similarity