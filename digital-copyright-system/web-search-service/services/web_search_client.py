import httpx  # untuk HTTP request
from config.settings import config  # ambil config
from services.cloudinary_client import upload_image, delete_image  # upload & delete image
from utils.logger import logger  # logger
from services.image_downloader import download_image  # download image kandidat
from services.feature_client import get_embedding  # ambil embedding dari feature service

SERPAPI_KEY = config["serpapi_key"]  # ambil API key


async def search_image(image_bytes):

    # 1. upload ke cloudinary
    image_url, public_id = upload_image(image_bytes)
    logger.info(f"Uploaded image to Cloudinary: {image_url}")

    try:
        # 2. call serpapi (Google Lens)
        params = {
            "engine": "google_lens",
            "url": image_url,
            "api_key": SERPAPI_KEY
        }

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.get(
                "https://serpapi.com/search",
                params=params
            )

            data = response.json()
            logger.info("SerpAPI response received")

        # 3. ambil kandidat + embedding
        visual_matches = data.get("visual_matches", [])

        matches = []

        for item in visual_matches[:5]:  # limit 5 biar tidak berat

            image_url_candidate = item.get("thumbnail")
            source_url = item.get("link")
            title = item.get("title", "")

            if not image_url_candidate:
                continue

            try:
                # 🔽 download image kandidat
                image_bytes_candidate = await download_image(image_url_candidate)

                # 🔽 kirim ke feature extraction service
                embedding = await get_embedding(image_bytes_candidate)

                match = {
                    "image_url": image_url_candidate,
                    "source_url": source_url,
                    "title": title,
                    "embedding": embedding  # 🔥 ini kunci untuk similarity
                }

                matches.append(match)

            except Exception as e:
                logger.warning(f"Skip candidate {image_url_candidate}: {str(e)}")

        logger.info(f"Processed {len(matches)} candidate images")

        return {
            "found_on_web": len(matches) > 0,
            "matches": matches
        }

    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")

        return {
            "found_on_web": False,
            "matches": []
        }

    finally:
        # 4. hapus dari cloudinary (cleanup)
        delete_image(public_id)
        logger.info("Temporary image deleted from Cloudinary")