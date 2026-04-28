from typing import Optional  # Import Optional untuk form yang tidak wajib diisi

from fastapi import APIRouter, File, Form, Request, UploadFile  # Import router, request, dan multipart tools FastAPI

from utils.proxy import proxy_multipart_request, proxy_request  # Import helper proxy reusable


router = APIRouter(tags=["gateway"])  # Membuat router untuk endpoint gateway


@router.post("/upload")  # Endpoint gateway untuk upload gambar
async def upload(  # Handler request upload
    request: Request,  # Request asli dari client
    file: UploadFile = File(...),  # File gambar wajib dikirim dengan field bernama file
    preset: Optional[str] = Form(None),  # Preset threshold opsional
    high_threshold: Optional[float] = Form(None),  # Custom high threshold opsional
    medium_threshold: Optional[float] = Form(None),  # Custom medium threshold opsional
    low_threshold: Optional[float] = Form(None),  # Custom low threshold opsional
):  # Menutup parameter upload
    # Main pipeline entrypoint: upload-service orchestrates the full workflow.
    return await proxy_multipart_request(  # Forward multipart ke upload-service
        request,  # Request asli dari client
        "upload-service",  # Nama upstream service tujuan
        "/upload",  # Path endpoint upload-service
        "file",  # Nama field file sesuai kontrak upload-service
        file,  # File gambar dari client
        {  # Form data tambahan yang diteruskan ke upload-service
            "preset": preset,  # Preset threshold
            "high_threshold": high_threshold,  # Custom high threshold
            "medium_threshold": medium_threshold,  # Custom medium threshold
            "low_threshold": low_threshold,  # Custom low threshold
        },  # Menutup form data tambahan
    )  # Menutup proxy multipart upload


# @router.post("/features/extract")  # Endpoint gateway untuk ekstraksi fitur
# async def extract_features(  # Handler request ekstraksi fitur
#     request: Request,  # Request asli dari client
#     file: UploadFile = File(...),  # File gambar wajib dikirim dengan field bernama file
# ):  # Menutup parameter extract_features
#     # Direct proxy for generating CLIP and CNN embeddings.
#     return await proxy_multipart_request(  # Forward multipart ke feature service
#         request,  # Request asli dari client
#         "feature-extraction-service",  # Nama upstream service tujuan
#         "/extract",  # Path endpoint feature service
#         "file",  # Nama field file sesuai kontrak feature service
#         file,  # File gambar dari client
#     )  # Menutup proxy multipart feature extraction


# @router.post("/web-search/search")  # Endpoint gateway untuk web search
# async def search_web(  # Handler request web search
#     request: Request,  # Request asli dari client
#     image: UploadFile = File(...),  # File gambar wajib dikirim dengan field bernama image
# ):  # Menutup parameter search_web
#     # Direct proxy for external reverse image search.
#     return await proxy_multipart_request(  # Forward multipart ke web-search-service
#         request,  # Request asli dari client
#         "web-search-service",  # Nama upstream service tujuan
#         "/search",  # Path endpoint web-search-service
#         "image",  # Nama field file sesuai kontrak web-search-service
#         image,  # File gambar dari client
#     )  # Menutup proxy multipart web search


# @router.api_route("/similarity", methods=["POST"])  # Endpoint gateway untuk similarity check
# async def similarity(request: Request):  # Handler request similarity
#     # Direct proxy for internal and external similarity scoring.
#     return await proxy_request(request, "similarity-check-service", "/similarity")  # Forward ke similarity service


# @router.api_route("/decision", methods=["POST"])  # Endpoint gateway untuk decision engine
# async def decision(request: Request):  # Handler request decision
#     # Direct proxy for risk-level decision calculation.
#     return await proxy_request(request, "decision-engine", "/decision")  # Forward ke decision-engine
