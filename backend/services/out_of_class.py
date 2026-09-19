# Minimum top-1 confidence for a prediction to be trusted. Calibrated on held-out photos
# (ml/models/metrics.json): correct predictions have median confidence 0.84, wrong ones 0.52,
# and 0.3 rejects <1% of images. This only catches *uncertain* predictions - a confident
# call on a disease outside the 8 trained classes cannot be detected this way.
THRESHOLD = 0.3


def detect_unknown_disease(top_3_predictions):
    _, highest_confidence = top_3_predictions[0]
    return highest_confidence < THRESHOLD
