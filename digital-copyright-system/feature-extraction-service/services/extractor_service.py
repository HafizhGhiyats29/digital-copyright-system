import os  # Operasi path dan file
from models.phash import compute_phash  # Import fungsi pHash
from models.dhash import compute_dhash  # Import fungsi dHash
from models.embedding_cnn import ResNetEmbedding  # Import kelas embedding ResNet
from utils.preprocessing import save_upload_to_temp, load_pil_image  # Util helper untuk file

# Inisialisasi extractor sekali saat service start
extractor = ResNetEmbedding()  # Buat instance ResNetEmbedding

async def process_upload_file(upload_file) -> dict:
    """
    Proses UploadFile dari FastAPI:
    1) Simpan sementara,
    2) Validasi & load PIL,
    3) Hitung pHash, dHash, dan embedding.
    """
    # Simpan file yang diupload ke folder temp dan kembalikan path
    local_path = await save_upload_to_temp(upload_file)  # Simpan file sementara
    # Load PIL Image dari path
    pil_image = load_pil_image(local_path)  # Baca file menjadi PIL Image
    # Hitung pHash dan dHash
    phash = compute_phash(pil_image)  # Hitung pHash
    dhash = compute_dhash(pil_image)  # Hitung dHash
    # Ekstrak embedding (numpy array)
    embedding = extractor.extract_from_path(local_path)  # Ekstrak embedding dengan ResNet
    # (Opsional) hapus file sementara bila tidak diperlukan
    try:
        os.remove(local_path)  # Hapus file temporer untuk hemat disk
    except Exception:
        pass  # Bila gagal menghapus, lewati
    # Kembalikan hasil dalam bentuk serializable (list untuk embedding)
    return {
        "phash": phash,
        "dhash": dhash,
        "embedding_dim": int(embedding.shape[0]),
        "embedding": embedding.tolist()
    }
