import sys  # Mengakses konfigurasi path Python
from pathlib import Path  # Mengatur path folder dan file
import mimetypes  # Menebak tipe file berdasarkan ekstensi
import httpx  # HTTP client untuk request ke feature-extraction-service
from pymilvus import connections  # Membuat koneksi ke Milvus
from pymilvus import utility  # Mengecek collection Milvus
from pymilvus import Collection  # Mengakses collection Milvus

ROOT_DIR = Path(__file__).resolve().parents[1]  # Mengambil folder root similarity-check-service
sys.path.append(str(ROOT_DIR))  # Menambahkan root project ke Python path

from config.settings import settings  # Mengambil konfigurasi dari settings.yaml


MILVUS_HOST = settings["milvus_host"]  # Host Milvus
MILVUS_PORT = settings["milvus_port"]  # Port Milvus
COLLECTION_NAME = settings["milvus_collection_name"]  # Nama collection Milvus
FEATURE_SERVICE_URL = settings["feature_service_url"]  # URL feature-extraction-service
INTERNAL_IMAGES_DIR = (ROOT_DIR / settings["internal_images_dir"]).resolve()  # Path folder gambar internal


def connect_milvus():  # Fungsi untuk koneksi ke Milvus
    connections.connect(  # Membuka koneksi Milvus
        alias="default",  # Alias koneksi default
        host=MILVUS_HOST,  # Host Milvus
        port=MILVUS_PORT  # Port Milvus
    )  # Menutup koneksi Milvus


def get_image_files():  # Fungsi mengambil semua file gambar internal
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}  # Ekstensi gambar yang didukung

    image_files = [  # Membuat list file gambar
        file_path  # File gambar yang valid
        for file_path in INTERNAL_IMAGES_DIR.iterdir()  # Loop semua file di folder internal_images
        if file_path.suffix.lower() in allowed_extensions  # Filter hanya ekstensi gambar
    ]  # Menutup list comprehension

    return image_files  # Mengembalikan list gambar


def extract_feature(image_path):  # Fungsi request embedding ke feature-extraction-service
    image_bytes = image_path.read_bytes()  # Membaca gambar menjadi bytes

    mime_type = mimetypes.guess_type(image_path.name)[0]  # Menebak MIME type gambar
    mime_type = mime_type or "image/jpeg"  # Default ke image/jpeg jika gagal ditebak

    files = {  # Membuat multipart form-data
        "file": (image_path.name, image_bytes, mime_type)  # Field harus "file" sesuai feature_router.py
    }  # Menutup dictionary files

    with httpx.Client(timeout=120.0) as client:  # Membuat HTTP client dengan timeout 120 detik
        response = client.post(  # Mengirim POST request ke feature service
            FEATURE_SERVICE_URL,  # URL endpoint /extract
            files=files  # File gambar yang dikirim
        )  # Menutup request

        response.raise_for_status()  # Lempar error jika response bukan 2xx

        result = response.json()  # Mengambil response JSON

    return result  # Mengembalikan hasil feature extraction


def insert_images_to_milvus():  # Fungsi utama insert gambar internal ke Milvus
    connect_milvus()  # Koneksi ke Milvus

    if not utility.has_collection(COLLECTION_NAME):  # Cek apakah collection sudah ada
        raise RuntimeError(f"Collection '{COLLECTION_NAME}' belum ada. Jalankan create_milvus_collection.py dulu.")  # Error jika belum ada

    collection = Collection(COLLECTION_NAME)  # Membuka collection Milvus

    image_files = get_image_files()  # Mengambil semua gambar internal

    if not image_files:  # Cek apakah folder kosong
        print(f"Tidak ada gambar di folder: {INTERNAL_IMAGES_DIR}")  # Info folder kosong
        return  # Hentikan proses

    image_ids = []  # List untuk image_id
    image_urls = []  # List untuk image_url/path
    titles = []  # List untuk title
    owners = []  # List untuk owner
    clip_embeddings = []  # List untuk embedding CLIP
    cnn_embeddings = []  # List untuk embedding CNN

    for image_path in image_files:  # Loop semua gambar internal
        print(f"Processing: {image_path.name}")  # Log gambar yang sedang diproses

        feature = extract_feature(image_path)  # Ambil CLIP + CNN embedding dari feature-service

        clip_embedding = feature.get("clip_embedding")  # Ambil embedding CLIP
        cnn_embedding = feature.get("cnn_embedding")  # Ambil embedding CNN

        if not clip_embedding or not cnn_embedding:  # Validasi embedding lengkap
            print(f"Skip {image_path.name}: embedding tidak lengkap")  # Log skip
            continue  # Lanjut ke gambar berikutnya

        if len(clip_embedding) != 512:  # Validasi dimensi CLIP
            print(f"Skip {image_path.name}: dimensi CLIP salah = {len(clip_embedding)}")  # Log dimensi salah
            continue  # Lanjut ke gambar berikutnya

        if len(cnn_embedding) != 2048:  # Validasi dimensi CNN
            print(f"Skip {image_path.name}: dimensi CNN salah = {len(cnn_embedding)}")  # Log dimensi salah
            continue  # Lanjut ke gambar berikutnya

        image_ids.append(image_path.stem)  # Simpan image_id dari nama file tanpa ekstensi
        image_urls.append(str(image_path))  # Simpan path gambar sebagai image_url lokal
        titles.append(image_path.stem)  # Simpan title dari nama file
        owners.append("internal_organization")  # Simpan owner default
        clip_embeddings.append(clip_embedding)  # Simpan embedding CLIP
        cnn_embeddings.append(cnn_embedding)  # Simpan embedding CNN

    if not image_ids:  # Cek apakah tidak ada data valid
        print("Tidak ada gambar valid untuk dimasukkan ke Milvus")  # Log tidak ada data
        return  # Hentikan proses

    insert_data = [  # Data insert harus mengikuti urutan field non-auto_id
        image_ids,  # Field image_id
        image_urls,  # Field image_url
        titles,  # Field title
        owners,  # Field owner
        clip_embeddings,  # Field clip_embedding
        cnn_embeddings  # Field cnn_embedding
    ]  # Menutup list insert_data

    collection.insert(insert_data)  # Insert data ke Milvus
    collection.flush()  # Memastikan data tersimpan
    collection.load()  # Load collection agar siap untuk search

    print(f"Berhasil insert {len(image_ids)} gambar ke Milvus")  # Log jumlah insert sukses
    print(f"Total entities sekarang: {collection.num_entities}")  # Log total data dalam collection


if __name__ == "__main__":  # Entry point script
    insert_images_to_milvus()  # Jalankan proses insert gambar internal