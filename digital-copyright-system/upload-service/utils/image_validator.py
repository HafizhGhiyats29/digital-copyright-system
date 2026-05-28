import io  # library manipulasi byte

from PIL import Image, UnidentifiedImageError  # library untuk memproses gambar


ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}  # Format gambar yang didukung sistem
MAX_IMAGE_PIXELS = 40_000_000  # Batas piksel untuk mencegah gambar sangat besar/decompression bomb


def validate_image(file_bytes):  # fungsi validasi gambar
    if not file_bytes:  # File kosong tidak boleh diproses
        raise ValueError("File gambar kosong")

    try:
        image = Image.open(io.BytesIO(file_bytes))  # membuka gambar dari memory
        image_format = image.format  # Ambil format asli dari isi file, bukan header request
        width, height = image.size  # Ambil dimensi gambar untuk validasi ukuran piksel

        if image_format not in ALLOWED_IMAGE_FORMATS:  # Tolak format selain JPEG/PNG/WEBP
            raise ValueError("Format gambar harus JPG, PNG, atau WEBP")

        if width <= 0 or height <= 0:  # Validasi dimensi dasar
            raise ValueError("Dimensi gambar tidak valid")

        if width * height > MAX_IMAGE_PIXELS:  # Cegah gambar dengan dimensi terlalu besar
            raise ValueError("Resolusi gambar terlalu besar")

        image.verify()  # memastikan file adalah gambar valid
    except UnidentifiedImageError as exc:
        raise ValueError("File bukan gambar yang valid") from exc
    except OSError as exc:
        raise ValueError("File gambar rusak atau tidak dapat dibaca") from exc

    return True
