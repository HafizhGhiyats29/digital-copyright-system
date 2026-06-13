import torch  # Library PyTorch untuk inference model
from torchvision import transforms
from models.clipcnn_model import cnn_model, device  # Import model dan device
from utils.image_utils import letterbox_image


cnn_transform = transforms.Compose([
    transforms.Lambda(letterbox_image),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def extract_cnn_embedding(image):  # Fungsi untuk mengambil embedding CNN dari gambar PIL
    image_tensor = cnn_transform(image).unsqueeze(0).to(device)  # Preprocess gambar dan tambah batch dimension

    with torch.no_grad():  # Matikan gradient agar inference lebih ringan
        features = cnn_model(image_tensor)  # Ambil fitur visual dari CNN

    features = features / features.norm(dim=-1, keepdim=True)  # Normalisasi embedding CNN
    embedding = features.squeeze().cpu().tolist()  # Ubah tensor menjadi list Python

    return embedding  # Kembalikan embedding CNN
