import torch  # Pustaka PyTorch

def get_device():
    """Kembalikan device yang akan digunakan (cuda jika tersedia, else cpu)."""
    return "cuda" if torch.cuda.is_available() else "cpu"  # Return string device
