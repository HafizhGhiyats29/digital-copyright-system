from transformers import CLIPProcessor, CLIPModel  # load CLIP
import torch  # untuk tensor

# load model sekali saja (global)
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)


def get_model():
    return model, processor, device