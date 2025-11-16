from PIL import Image  # Memanggil PIL.Image untuk manipulasi gambar
import imagehash  # Memanggil pustaka imagehash untuk dHash

def compute_dhash(image: Image.Image):
    """Hitung difference hash (dHash) dari objek PIL Image."""
    return str(imagehash.dhash(image))  # Kembalikan dHash sebagai string hex
