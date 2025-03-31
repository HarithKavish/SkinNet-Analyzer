import torch
import torchvision.transforms as transforms
from PIL import Image
import requests
from io import BytesIO

# Load pre-trained EfficientNet model for severity estimation
severity_model = torch.load("models/severity_model.pth", map_location=torch.device('cpu'), weights_only=False)
severity_model.eval()

# Preprocess image
def preprocess_for_severity(image_url):
    # response = requests.get(image_url)
    # image = Image.open(BytesIO(response.content)).convert("RGB")
    image = Image.open(BytesIO(image_url)).convert("RGB")
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    
    return transform(image).unsqueeze(0)

# Severity estimation
def estimate_severity(image_url, disease):
    
    with open(image_url, "rb") as img_file:
        image_bytes = img_file.read()  # Read the image as binary data
        
    image_tensor = preprocess_for_severity(image_bytes)

    with torch.no_grad():
        severity_score = severity_model(image_tensor).item()

    if severity_score < 0.3:
        return "Mild"
    elif severity_score < 0.7:
        return "Moderate"
    else:
        return "Severe"
