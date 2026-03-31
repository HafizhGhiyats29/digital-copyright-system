from pydantic import BaseModel  # library schema validation


class UploadResponse(BaseModel):  # schema response upload

    status: str  # status proses
    web_search_result: dict  # hasil dari web search