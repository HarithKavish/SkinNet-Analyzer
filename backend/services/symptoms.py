import math


# Define symptom equivalences
equivalent_symptoms = {
    #Systemic Symptoms
    "fever": ["fever"],
    "fatigue/tiredness": ["tiredness", "fatigue"],
    "pain": ["pain", "burning pain", "nerve pain", "painful swelling"],
    
    #Inside-skin Symptoms
    "burning/itching": ["itching", "burning"],
    
    #On-skin Symptoms
    "sores": ["sores"],
    "crusting": ["crusting"],
    "swelling/inflammation": ["swelling", "painful swelling", "inflammation"],
    "blisters": ["blisters", "fluid-filled blisters"],
    "warm skin": ["warm skin"],
    
    #Over-skin Symptoms
    "redness": ["redness", "red ring-shaped patch"],
    "thread/ring like pattern": ["red ring-shaped patch", "red lines on skin"],
    "skin texture changes": ["peeling skin", "scaly skin", "cracks"],
    "nail changes": ["thickened nails", "nail discoloration", "brittle nails"],
    "bad odor": ["bad odor"]
}

def normalize_symptom(symptom):
    for key, values in equivalent_symptoms.items():
        if symptom in values:
            return key
    return symptom

# Disease symptom mapping
SYMPTOM_MAPPING = {
    "Cellulitis": ["redness", "swelling", "warm skin", "pain",   "fever"],
    "Impetigo": ["sores", "itching", "blisters", "crusting"],
    "Ringworm": ["red ring-shaped patch", "itching", "scaly skin",   "inflammation"],
    "Cutaneous-larva-migrans": ["itching", "red lines on skin",   "painful swelling"],
    "Chickenpox": ["fever", "tiredness", "itching",   "fluid-filled blisters"],
    "Shingles": ["burning pain", "itching", "blisters",   "nerve pain"],
    "Athlete-foot": ["itching", "cracks", "burning", "peeling skin",   "blisters"],
    "Nail-fungus": ["thickened nails", "nail discoloration", "brittle nails",   "bad odor"]
}

# Normalize disease symptoms
SYMPTOM_MAPPING = {
    disease: list(set(normalize_symptom(symptom) for symptom in symptoms))
    for disease, symptoms in SYMPTOM_MAPPING.items()
}

def confirm_disease_with_symptoms(top_3_predictions):
    """
    Sends symptom questions to the frontend for user input.
    Returns (questions, disease_keys) - disease_keys must be echoed back by the
    client in process_user_responses, since this backend runs multiple worker
    processes with no shared memory between requests.
    """
    disease_keys = [disease for disease, _ in top_3_predictions]

    for disease, symptoms in SYMPTOM_MAPPING.items():
        print(disease," : ",symptoms)

    # Collect unique symptoms from the top diseases
    unique_symptoms = set()
    for disease in disease_keys:
        if disease in SYMPTOM_MAPPING:
            unique_symptoms.update(SYMPTOM_MAPPING[disease])

    # Convert unique symptoms into a dictionary with questions
    questions = {symptom: f"Do you have {symptom}?" for symptom in unique_symptoms}

    return questions, disease_keys

# Assumed chance that one Yes/No answer is right. Deliberately low: simulations showed the
# photo should keep a real vote, so a few wrong answers cannot override a confident photo.
ANSWER_RELIABILITY = 0.7
# Below this photo confidence, a disease with almost none of its symptoms confirmed is
# treated as out of class (no report). A confident photo is never blocked by sparse answers.
OUT_OF_CLASS_PHOTO_CONFIDENCE = 0.5


def process_user_responses(disease_keys, answers, probabilities=None):
    """
    Confirms the most probable disease by combining the photo with the symptom answers.

    Each candidate scores log(photo probability) + how well the answers agree with that
    disease's symptom list (a Yes for a symptom it has, or a No for one it lacks, counts as
    agreement). Questions the user did not answer are ignored. `probabilities` are the
    photo's confidences in the same order as disease_keys; without them the candidates
    start equal, so only the answers decide.
    """
    if not probabilities or len(probabilities) != len(disease_keys):
        probabilities = [1.0 / len(disease_keys)] * len(disease_keys)

    answered = {symptom: value == "1" for symptom, value in answers.items()}
    log_right, log_wrong = math.log(ANSWER_RELIABILITY), math.log(1 - ANSWER_RELIABILITY)

    scores = {}
    for disease, probability in zip(disease_keys, probabilities):
        symptoms = SYMPTOM_MAPPING.get(disease, [])
        agree = sum((symptom in symptoms) == yes for symptom, yes in answered.items())
        scores[disease] = math.log(probability + 1e-9) + agree * log_right + (len(answered) - agree) * log_wrong

    confirmed_disease = max(scores, key=scores.get)  # ties keep the photo's own ranking
    confirmed_symptoms = SYMPTOM_MAPPING.get(confirmed_disease, [])
    matched = sum(1 for symptom in confirmed_symptoms if answered.get(symptom))
    severity_percentage = matched / len(confirmed_symptoms) if confirmed_symptoms else 0.0
    photo_confidence = probabilities[disease_keys.index(confirmed_disease)]

    if severity_percentage < 0.25:
        severity = "Out of Class" if photo_confidence < OUT_OF_CLASS_PHOTO_CONFIDENCE else "Mild"
    elif severity_percentage <= 0.50:
        severity = "Mild"
    elif severity_percentage < 0.75:
        severity = "Moderate"
    else:
        severity = "Severe"

    print("Disease Scores: ", scores)
    print("Confirmed Disease:", confirmed_disease, "| photo confidence:", round(photo_confidence, 2),
          "| symptoms matched:", f"{matched}/{len(confirmed_symptoms)}", "| severity:", severity)
    return confirmed_disease, severity
