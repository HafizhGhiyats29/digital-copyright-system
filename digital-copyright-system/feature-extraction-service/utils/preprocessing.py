import os  # Operasi file/path
import uuid  # Untuk membuat nama file unik
from PIL import Image  # Untuk buka & validasi gambar
from fastapi import UploadFile  # Tipe UploadFile dari FastAPI

TEMP_DIR = os.getenv("TEMP_DIR", "./temp")  # Folder temporer default
os.makedirs(TEMP_DIR, exist_ok=True)  # Pastikan folder ada

async def save_upload_to_temp(upload_file: UploadFile) -> str:
    """Simpan UploadFile ke file temporer dan kembalikan path-nya."""
    # Buat nama file unik untuk menghindari tabrakan
    ext = os.path.splitext(upload_file.filename)[1]  # Ambil ekstensi file
    tmp_name = f"{uuid.uuid4().hex}{ext}"  # Nama file sementara
    tmp_path = os.path.join(TEMP_DIR, tmp_name)  # Path lengkap file sementara
    # Tulis konten file ke disk
    with open(tmp_path, "wb") as f:
        content = await upload_file.read()  # Baca seluruh konten upload
        f.write(content)  # Simpan ke file
    return tmp_path  # Kembalikan path file yang disimpan

def load_pil_image(path: str) -> Image.Image:
    """Muat file dari path dan kembalikan objek PIL Image (juga melakukan verifikasi dasar)."""
    img = Image.open(path)  # Buka file sebagai PIL Image
    img.verify()  # Verifikasi format; akan raise jika file korup
    # Buka ulang karena verify() bisa membuat file tidak dalam mode read yang normal
    return Image.open(path).convert("RGB")  # Kembalikan PIL Image dalam mode RGB

def is_image_file(path: str) -> bool:
    """Cek apakah path berisi file dengan ekstensi gambar yang didukung."""
    try:
        img = Image.open(path)  # Coba buka file
        img.verify()  # Verifikasi
        return True  # Jika sukses, artinya file adalah gambar
    except Exception:
        return False  # Bukan gambar valid
