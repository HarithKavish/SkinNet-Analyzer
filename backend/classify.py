import torch
import torchvision.transforms as transforms
from PIL import Image
import requests
import numpy as np
from io import BytesIO

# Load trained models
efficientnet = torch.load("models/efficientnet.pth", map_location=torch.device('cpu'), weights_only=False)
resnet = torch.load("models/resnet.pth", map_location=torch.device('cpu'), weights_only=False)
mobilenet = torch.load("models/mobilenet.pth", map_location=torch.device('cpu'), weights_only=False)

efficientnet.eval()
resnet.eval()
mobilenet.eval()

# Class Labels
classes = ["Cellulitis", "Impetigo", "Athlete-foot", "Nail-fungus",
           "Ringworm", "Cutaneous-larva-migrans", "Chickenpox", "Shingles"]

# Preprocess the image
def preprocess_image(response):
    # image = Image.open(BytesIO(response.content)).convert("RGB")
    image = Image.open(BytesIO(response)).convert("RGB")
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    
    return transform(image).unsqueeze(0)  # Add batch dimension

# Ensemble classification
def ensemble_classify(image_url):
    # response = requests.get(image_url)
    
    with open(image_url, "rb") as img_file:
        image_bytes = img_file.read()  # Read the image as binary data
    
    image_tensor = preprocess_image(image_bytes)

    # Get predictions from each model
    with torch.no_grad():
        output1 = efficientnet(image_tensor)
        output2 = resnet(image_tensor)
        output3 = mobilenet(image_tensor)

    # Average the predictions
    final_output = (output1 + output2 + output3) / 3
    probabilities = torch.nn.functional.softmax(final_output, dim=1).squeeze().tolist()

    # Get top 3 predictions
    top_3_indices = sorted(range(len(probabilities)), key=lambda i: probabilities[i], reverse=True)[:3]
    top_3_predictions = [(classes[i], probabilities[i]) for i in top_3_indices]

    return top_3_predictions
