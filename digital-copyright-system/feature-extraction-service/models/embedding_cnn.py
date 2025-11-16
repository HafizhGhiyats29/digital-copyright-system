import torch  # Memanggil PyTorch sebagai torch
import torch.nn as nn  # Memanggil modul neural network PyTorch
import torchvision.models as models  # Memanggil model pretrained dari torchvision
import torchvision.transforms as transforms  # Memanggil transformasi gambar dari torchvision
from PIL import Image  # Memanggil PIL.Image untuk membuka gambar

class ResNetEmbedding:
    """Kelas pembungkus ResNet50 untuk mengekstraksi embedding vektor."""
    def __init__(self, device: str = None):
        # Load ResNet50 pretrained; gunakan weights default jika tersedia
        self.model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)  # Muat model ResNet50 pra-latih
        self.model = nn.Sequential(*list(self.model.children())[:-1])  # Hapus fully-connected terakhir untuk dapat embedding
        self.model.eval()  # Set model ke mode evaluasi (non-training)
        # Preprocessing yang sesuai dengan ResNet/ImageNet
        self.transform = transforms.Compose([  # Rangkaian preprocessing
            transforms.Resize((224, 224)),  # Ubah ukuran gambar menjadi 224x224
            transforms.ToTensor(),  # Konversi gambar ke tensor PyTorch
            transforms.Normalize(  # Normalisasi menggunakan mean/std ImageNet
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        # Tentukan device: parameter > env > fallback cpu
        if device:
            self.device = torch.device(device)  # Gunakan device yang diberikan
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Gunakan CUDA bila tersedia
        self.model.to(self.device)  # Pindahkan model ke device yang dipilih

    def extract_from_pil(self, image: Image.Image):
        """Ekstrak embedding dari objek PIL Image dan kembalikan numpy array 1D."""
        img = image.convert("RGB")  # Pastikan gambar dalam mode RGB
        img_t = self.transform(img).unsqueeze(0).to(self.device)  # Preprocess dan tambahkan dimensi batch
        with torch.no_grad():  # Nonaktifkan gradient untuk inference
            emb = self.model(img_t)  # Forward pass → shape (1, 2048, 1, 1)
            emb = emb.squeeze()  # Hapus dimensi ekstra → shape (2048,)
            emb = emb.cpu().numpy()  # Pindahkan ke CPU dan ubah ke numpy array
        return emb  # Kembalikan vektor embedding sebagai numpy array

    def extract_from_path(self, image_path: str):
        """Baca file gambar dari path lalu panggil ekstraksi PIL."""
        img = Image.open(image_path)  # Buka file gambar
        return self.extract_from_pil(img)  # Ekstrak embedding dari PIL Image
