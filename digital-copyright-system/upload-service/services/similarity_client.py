import httpx  # Import HTTP client async
from config.settings import config  # Import config


SIMILARITY_SERVICE_URL = config["similarity_service_url"]  # Ambil URL similarity-service dari config


async def send_to_similarity(query_clip_embedding, query_cnn_embedding, web_matches):  # Fungsi kirim data ke similarity
    timeout = httpx.Timeout(60.0)  # Timeout request ke similarity-service

    async with httpx.AsyncClient(timeout=timeout) as client:  # Membuat HTTP client
        response = await client.post(  # Mengirim POST request
            SIMILARITY_SERVICE_URL,  # Endpoint similarity-service
            json={  # Body JSON request
                "clip_embedding": query_clip_embedding,  # Embedding CLIP gambar original
                "cnn_embedding": query_cnn_embedding,  # Embedding CNN gambar original
                "web_matches": web_matches  # Kandidat dari web-search-service
            }  # Menutup JSON body
        )  # Menutup request POST

        response.raise_for_status()  # Lempar error jika response bukan 2xx

        return response.json()  # Return hasil similarity