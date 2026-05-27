import httpx

from config.settings import config
from utils.internal_auth import internal_auth_headers


DECISION_SERVICE_URL = config["decision_service_url"]


async def send_to_decision(overall_score, clip_score=None, cnn_score=None, preset=None, thresholds=None):
    timeout = httpx.Timeout(30.0)
    body = {"overall_score": overall_score}

    if clip_score is not None:
        body["clip_score"] = clip_score

    if cnn_score is not None:
        body["cnn_score"] = cnn_score

    if preset is not None:
        body["preset"] = preset

    if thresholds is not None:
        body["thresholds"] = thresholds

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            DECISION_SERVICE_URL,
            json=body,
            headers=internal_auth_headers(),
        )
        response.raise_for_status()
        return response.json()
