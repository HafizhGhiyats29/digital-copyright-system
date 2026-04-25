import torch  # Library PyTorch untuk inference model
from torchvision import transforms  # Transformasi gambar untuk CNN
from models.clipcnn_model import cnn_model, device  # Import model CNN dan device
from config.settings import settings  # Import konfigurasi


cnn_transform = transforms.Compose([  # Pipeline preprocessing gambar untuk CNN
    transforms.Resize((settings["image_size"], settings["image_size"])),  # Resize gambar ke 224x224
    transforms.ToTensor(),  # Ubah PIL Image menjadi tensor
    transforms.Normalize(  # Normalisasi standar ImageNet
        mean=[0.485, 0.456, 0.406],  # Mean RGB ImageNet
        std=[0.229, 0.224, 0.225]  # Standar deviasi RGB ImageNet
    )  # Menutup Normalize
])  # Menutup Compose


def extract_cnn_embedding(image):  # Fungsi untuk mengambil embedding CNN dari gambar PIL
    image_tensor = cnn_transform(image).unsqueeze(0).to(device)  # Preprocess gambar dan tambah batch dimension

    with torch.no_grad():  # Matikan gradient agar inference lebih ringan
        features = cnn_model(image_tensor)  # Ambil fitur visual dari CNN

    features = features / features.norm(dim=-1, keepdim=True)  # Normalisasi embedding CNN
    embedding = features.squeeze().cpu().tolist()  # Ubah tensor menjadi list Python

    return embedding  # Kembalikan embedding CNN