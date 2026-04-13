import httpx  # untuk HTTP request
import asyncio  # untuk parallel async
from config.settings import config  # ambil config
from services.cloudinary_client import upload_image, delete_image  # cloudinary
from utils.logger import logger  # logger
from services.image_downloader import download_image  # download gambar
from services.feature_client import get_embedding  # extract embedding

SERPAPI_KEY = config["serpapi_key"]  # API key


async def process_candidate(item):
    image_url_candidate = item.get("thumbnail")  # ambil thumbnail
    source_url = item.get("link")  # link sumber
    title = item.get("title", "")  # judul

    if not image_url_candidate:
        return None  # skip jika tidak ada URL

    try:
        image_bytes = await download_image(image_url_candidate)  # download gambar
        embedding = await get_embedding(image_bytes)  # ambil embedding

        return {
            "image_url": image_url_candidate,
            "source_url": source_url,
            "title": title,
            "embedding": embedding  # hasil vector
        }

    except Exception as e:
        logger.warning(f"Skip candidate {image_url_candidate}: {str(e)}")  # log error
        return None  # skip jika gagal


async def search_image(image_bytes):

    # 1. upload ke cloudinary
    image_url, public_id = upload_image(image_bytes)  # upload gambar
    logger.info(f"Uploaded image to Cloudinary: {image_url}")  # log

    try:
        # 2. request ke SerpAPI (Google Lens)
        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": SERPAPI_KEY
        }

        timeout = httpx.Timeout(60.0)  # timeout aman

        async with httpx.AsyncClient(timeout=timeout) as client:  # client async
            response = await client.get(  # request GET
                "https://serpapi.com/search",
                params=params
            )

            data = response.json()  # ambil JSON
            logger.info("SerpAPI response received")  # log

        # 3. ambil kandidat gambar
        visual_matches = data.get("visual_matches", [])  # ambil list

        # 🔥 batasi kandidat (biar cepat)
        candidates = visual_matches[:3]  # dari 5 → 3

        # 🔥 PARALLEL PROCESSING
        tasks = [
            process_candidate(item) for item in candidates
        ]  # kumpulkan task

        results = await asyncio.gather(*tasks)  # jalankan paralel

        # filter hasil valid
        matches = [r for r in results if r is not None]

        logger.info(f"Processed {len(matches)} candidate images")  # log

        return {
            "found_on_web": len(matches) > 0,
            "matches": matches
        }

    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")  # log error

        return {
            "found_on_web": False,
            "matches": []
        }

    finally:
        # 4. cleanup cloudinary
        delete_image(public_id)  # hapus gambar
        logger.info("Temporary image deleted from Cloudinary")  # log