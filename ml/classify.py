import os

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

# Class Labels - order must match ml/train.py and models/class_indices.pkl
classes = ["Cellulitis", "Impetigo", "Athlete-foot", "Nail-fungus",
           "Ringworm", "Cutaneous-larva-migrans", "Chickenpox", "Shingles"]


def _load(model, name):
    state = torch.load(os.path.join(MODEL_DIR, f"{name}.pth"), map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    return model.eval()


# Same architectures as ml/train.py; weights are plain state_dicts, so loading does not depend
# on the exact torch/torchvision version that saved them.
efficientnet = models.efficientnet_b0(weights=None)
efficientnet.classifier[1] = nn.Linear(1280, len(classes))
efficientnet = _load(efficientnet, "efficientnet")

resnet = models.resnet18(weights=None)
resnet.fc = nn.Linear(512, len(classes))
resnet = _load(resnet, "resnet")

mobilenet = models.mobilenet_v2(weights=None)
mobilenet.classifier[1] = nn.Linear(1280, len(classes))
mobilenet = _load(mobilenet, "mobilenet")


# Preprocess the image (identical to the eval transform used in training)
def preprocess_image(image: Image.Image):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    return transform(image).unsqueeze(0)  # Add batch dimension


# Ensemble classification
def ensemble_classify(img: Image.Image) -> list:
    image_tensor = preprocess_image(img)

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
