NOTICE = "> AI-generated details are temporarily unavailable, so general information is shown instead.\n\n"

FALLBACK_INFO = {
    "Cellulitis": {
        "external": [
            "Red, swollen, warm and tender area of skin that spreads",
            "Tight, glossy-looking skin; sometimes blisters or dimpling",
        ],
        "internal": ["Fever and chills", "Tiredness", "Swollen lymph nodes near the area"],
        "care": [
            "See a doctor promptly - cellulitis usually needs prescription antibiotics",
            "Take the full antibiotic course even if it looks better",
            "Rest and keep the affected limb raised",
            "Keep the area clean and covered; mark the edge of the redness to track spread",
        ],
        "urgent": "redness spreads quickly, you develop a high fever, red streaks, or severe pain",
    },
    "Impetigo": {
        "external": [
            "Red sores that burst and form honey-coloured crusts, often around the nose and mouth",
            "Itching; sometimes fluid-filled blisters",
        ],
        "internal": ["Usually none", "Sometimes mild fever or swollen glands"],
        "care": [
            "See a doctor - antibiotic cream or tablets are usually needed",
            "Gently wash sores with soap and water and cover them",
            "Avoid scratching; keep nails short",
            "Wash hands often and do not share towels or bedding - it is contagious",
        ],
        "urgent": "sores spread, you have a fever, or there is no improvement after a few days of treatment",
    },
    "Athlete-foot": {
        "external": [
            "Itchy, scaly, red rash between the toes or on the soles",
            "Cracked or peeling skin, burning, sometimes blisters",
        ],
        "internal": ["Usually none"],
        "care": [
            "Use an over-the-counter antifungal cream or powder as directed",
            "Wash and dry feet thoroughly, especially between the toes",
            "Wear breathable footwear and change socks daily",
            "Avoid walking barefoot in public showers or pools",
        ],
        "urgent": "there is no improvement after 2 weeks, the skin is very painful or oozing, or you have diabetes",
    },
    "Nail-fungus": {
        "external": [
            "Thick, brittle or crumbly nails",
            "Yellow, brown or white discolouration, distorted shape, sometimes a bad odour",
        ],
        "internal": ["Usually none; the nail can become painful"],
        "care": [
            "See a doctor or dermatologist - treatment (medicated lacquer or tablets) takes months",
            "Keep nails short, clean and dry",
            "Wear breathable shoes and do not share nail clippers",
            "Treat any athlete's foot at the same time",
        ],
        "urgent": "the nail is painful, the skin around it is red or swollen, or you have diabetes",
    },
    "Ringworm": {
        "external": [
            "Ring-shaped, red, scaly patch with a raised edge and clearer centre",
            "Itching; hair loss if it affects the scalp",
        ],
        "internal": ["Usually none"],
        "care": [
            "Use an over-the-counter antifungal cream for 2-4 weeks, as directed",
            "Keep the area clean and dry",
            "Wash towels and bedding in hot water; do not share personal items",
            "Check pets - they can carry it",
        ],
        "urgent": "it affects the scalp or nails, spreads, or does not improve after 2 weeks",
    },
    "Cutaneous-larva-migrans": {
        "external": [
            "Raised, red, winding itchy track that slowly moves",
            "Intense itching; sometimes small blisters",
        ],
        "internal": ["Usually none"],
        "care": [
            "See a doctor - antiparasitic medication is usually prescribed",
            "Avoid scratching to prevent infection",
            "Avoid walking barefoot or lying on sand or soil that animals may have soiled",
        ],
        "urgent": "the area becomes very painful, swollen, or shows signs of infection like pus",
    },
    "Chickenpox": {
        "external": [
            "Itchy, fluid-filled blisters that appear in crops and then crust over",
            "Usually starts on the face, chest and back",
        ],
        "internal": ["Fever", "Tiredness and headache", "Loss of appetite"],
        "care": [
            "Rest and drink plenty of fluids",
            "Use calamine lotion and cool baths to ease itching; keep nails short",
            "Use paracetamol for fever (avoid aspirin in children)",
            "Stay away from others, especially pregnant women and newborns, until all blisters have crusted",
        ],
        "urgent": "the patient is an infant, pregnant, an adult, has a weak immune system, or has trouble breathing or a very high fever",
    },
    "Shingles": {
        "external": [
            "Painful, burning rash of blisters in a band on one side of the body or face",
            "Itching or tingling before the rash appears",
        ],
        "internal": ["Nerve pain", "Fever, headache and tiredness"],
        "care": [
            "See a doctor quickly - antiviral medicine works best if started within 72 hours",
            "Keep the rash clean, dry and loosely covered",
            "Use cool compresses and pain relief as advised by your doctor",
            "Avoid contact with pregnant women, newborns and people with weak immunity",
        ],
        "urgent": "the rash is near an eye, or the pain is severe or spreading",
    },
}

DEFAULT_INFO = {
    "external": ["Changes in skin colour, texture or swelling in the affected area", "Itching or pain"],
    "internal": ["Possibly fever or tiredness"],
    "care": ["Keep the area clean and dry", "Avoid scratching", "Do not share towels or clothing"],
    "urgent": "symptoms worsen, spread, or you develop a fever",
}


def _bullets(items):
    return "\n".join(f"- {item}" for item in items)


def fallback_disease_info(disease: str) -> str:
    info = FALLBACK_INFO.get(disease, DEFAULT_INFO)
    return (
        NOTICE
        + "**External symptoms**\n" + _bullets(info["external"]) + "\n\n"
        + "**Internal symptoms**\n" + _bullets(info["internal"]) + "\n\n"
        + "**Steps to take care of it**\n" + _bullets(info["care"]) + "\n\n"
        + f"**See a doctor urgently if** {info['urgent']}.\n\n"
        + "_This is general information, not a diagnosis. Please consult a doctor._"
    )
