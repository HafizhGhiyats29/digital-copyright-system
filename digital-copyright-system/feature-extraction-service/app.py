from fastapi import FastAPI, UploadFile, File, HTTPException  # Import FastAPI dan tipe file
from fastapi.responses import JSONResponse  # Untuk mengembalikan JSON response
from services.extractor_service import process_upload_file  # Fungsi proses utama
import uvicorn  # Uvicorn server

app = FastAPI(title="Feature Extraction Service")  # Inisialisasi aplikasi FastAPI

@app.post("/extract")
async def extract_endpoint(file: UploadFile = File(...)):
    """Endpoint utama untuk menerima upload gambar dan mengembalikan fitur."""
    # Validasi content type dasar
    if file.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="File must be an image")
    # Proses file upload (simpan sementara, hitung hash & embedding)
    result = await process_upload_file(file)  # Panggil service extractor
    return JSONResponse(content=result)  # Kembalikan hasil sebagai JSON

if __name__ == "__main__":
    # Jalankan server dev bila file ini dieksekusi langsung
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
