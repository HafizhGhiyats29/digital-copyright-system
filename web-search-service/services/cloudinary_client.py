import cloudinary
import cloudinary.uploader
from config.settings import config

cloudinary.config(
    cloud_name=config["cloudinary"]["cloud_name"],
    api_key=config["cloudinary"]["api_key"],
    api_secret=config["cloudinary"]["api_secret"]
)


def upload_image(file_bytes):
    result = cloudinary.uploader.upload(file_bytes)
    return result["secure_url"], result["public_id"]


def delete_image(public_id):
    cloudinary.uploader.destroy(public_id)