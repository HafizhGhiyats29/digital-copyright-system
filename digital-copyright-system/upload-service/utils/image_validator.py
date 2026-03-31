from PIL import Image  # library untuk memproses gambar
import io  # library manipulasi byte


def validate_image(file_bytes):  # fungsi validasi gambar

    image = Image.open(io.BytesIO(file_bytes))  # membuka gambar dari memory
    image.verify()  # memastikan file adalah gambar valid

    return True