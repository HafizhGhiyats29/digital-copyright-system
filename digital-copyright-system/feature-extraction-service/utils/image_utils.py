from PIL import Image  # Library untuk membaca dan memproses gambar
import io  # Library untuk membaca bytes sebagai file


def load_image_from_bytes(image_bytes):  # Fungsi untuk membaca bytes gambar menjadi PIL Image
    image = Image.open(io.BytesIO(image_bytes))  # Membuka gambar dari bytes
    image = image.convert("RGB")  # Mengubah gambar menjadi RGB
    return image  # Mengembalikan gambar PIL