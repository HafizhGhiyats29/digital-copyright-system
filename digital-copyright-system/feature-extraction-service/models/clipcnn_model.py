import torch  # Library utama untuk deep learning
import torch.nn as nn  # Modul neural network PyTorch
from transformers import CLIPModel, CLIPProcessor  # Import CLIPModel penuh, bukan CLIPVisionModel
from torchvision import models  # Import model CNN dari torchvision
from config.settings import settings  # Import konfigurasi YAML


device = torch.device(  # Menentukan device yang digunakan
    settings["device"] if torch.cuda.is_available() and settings["device"] == "cuda" else "cpu"  # Gunakan CUDA jika tersedia
)  # Menutup pemilihan device


clip_model = CLIPModel.from_pretrained(settings["clip_model_name"]).to(device)  # Load CLIPModel penuh ke device
clip_processor = CLIPProcessor.from_pretrained(settings["clip_model_name"])  # Load processor CLIP


cnn_model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)  # Load ResNet50 pretrained
cnn_model.fc = nn.Identity()  # Buang layer classifier agar output menjadi embedding
cnn_model = cnn_model.to(device)  # Pindahkan CNN ke device


clip_model.eval()  # Mode evaluasi untuk CLIP
cnn_model.eval()  # Mode evaluasi untuk CNN