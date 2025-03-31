THRESHOLD = 0.4  # Adjust this based on dataset confidence

def detect_unknown_disease(top_3_predictions):
    _, highest_confidence = top_3_predictions[0]
    if highest_confidence < THRESHOLD:
        return True  # Disease not in the 8 classes
    return False
