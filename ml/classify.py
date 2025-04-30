import torch
from torch.serialization import safe_globals
import torchvision.transforms as transforms
from PIL import Image

# Allow EfficientNet to be safely unpickled
safe_globals(["torchvision.models.efficientnet.EfficientNet"])

# Load full models directly
efficientnet = torch.load("models/efficientnet.pth", map_location=torch.device("cpu"), weights_only=False)
efficientnet.eval()

resnet = torch.load("models/resnet.pth", map_location=torch.device("cpu"), weights_only=False)
resnet.eval()

mobilenet = torch.load("models/mobilenet.pth", map_location=torch.device("cpu"), weights_only=False)
mobilenet.eval()

# Class Labels
classes = ["Cellulitis", "Impetigo", "Athlete-foot", "Nail-fungus",
           "Ringworm", "Cutaneous-larva-migrans", "Chickenpox", "Shingles"]

# Preprocess the image
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
