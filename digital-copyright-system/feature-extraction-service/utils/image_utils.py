from PIL import Image, ImageOps  # Library untuk membaca, memperbaiki orientasi, dan memproses gambar
import io  # Library untuk membaca bytes sebagai file


MODEL_IMAGE_SIZE = 224
IMAGENET_PADDING_COLOR = (124, 116, 104)


def load_image_from_bytes(image_bytes):  # Fungsi untuk membaca bytes gambar menjadi PIL Image
    image = Image.open(io.BytesIO(image_bytes))  # Membuka gambar dari bytes
    image = ImageOps.exif_transpose(image)  # Terapkan orientasi EXIF sebelum preprocessing model
    image = image.convert("RGB")  # Mengubah gambar menjadi RGB
    return image  # Mengembalikan gambar PIL


def letterbox_image(image, size=MODEL_IMAGE_SIZE):
    """Resize proporsional dan tambahkan padding tanpa membuang bagian gambar."""
    return ImageOps.pad(
        image,
        (size, size),
        method=Image.Resampling.LANCZOS,
        color=IMAGENET_PADDING_COLOR,
        centering=(0.5, 0.5),
    )
