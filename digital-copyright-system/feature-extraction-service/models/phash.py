from PIL import Image  # Memanggil PIL.Image untuk manipulasi gambar
import imagehash  # Memanggil pustaka imagehash untuk pHash

def compute_phash(image: Image.Image):
    """Hitung perceptual hash (pHash) dari objek PIL Image."""
    return str(imagehash.phash(image))  # Kembalikan pHash sebagai string hex
