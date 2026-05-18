import httpx  # Mengimpor HTTP client async
from config.settings import config  # Mengimpor config aplikasi


DECISION_SERVICE_URL = config["decision_service_url"]  # Mengambil URL decision-engine dari config


async def send_to_decision(overall_score, clip_score=None, cnn_score=None, preset=None, thresholds=None):  # Fungsi kirim score ke decision-engine
    timeout = httpx.Timeout(30.0)  # Timeout request ke decision-engine

    body = {  # Membuat body request awal
        "overall_score": overall_score  # Mengirim overall_score dari similarity-service
    }  # Menutup dictionary body

    if clip_score is not None:  # Jika clip_score tersedia
        body["clip_score"] = clip_score  # Kirim clip_score ke decision-engine

    if cnn_score is not None:  # Jika cnn_score tersedia
        body["cnn_score"] = cnn_score  # Kirim cnn_score ke decision-engine

    if preset is not None:  # Mengecek apakah preset dikirim
        body["preset"] = preset  # Menambahkan preset ke body request

    if thresholds is not None:  # Mengecek apakah custom threshold dikirim
        body["thresholds"] = thresholds  # Menambahkan custom threshold ke body request

    async with httpx.AsyncClient(timeout=timeout) as client:  # Membuat HTTP client async
        response = await client.post(  # Mengirim request POST ke decision-engine
            DECISION_SERVICE_URL,  # URL endpoint /decision
            json=body  # Body JSON request
        )  # Menutup request POST

        response.raise_for_status()  # Menghasilkan error jika response bukan 2xx

        return response.json()  # Mengembalikan response JSON decision-engine
