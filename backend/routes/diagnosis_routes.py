from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict
import requests
from dotenv import load_dotenv
import os

from services.symptoms import confirm_disease_with_symptoms, process_user_responses
from services.out_of_class import detect_unknown_disease

router = APIRouter()

# Load environment variables from .env file
load_dotenv()

ML_API_URL = os.getenv("ML_API_URL")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if file.filename == "":
        raise HTTPException(status_code=400, detail="No selected file")

    response = requests.post(ML_API_URL,files={"file": ("image.jpg", await file.read(), file.content_type)})

    if response.status_code != 200:
        return JSONResponse(status_code=500, content={"error": "ML API failed"})

    top_3_predictions = response.json().get("predictions")

    print("Top 3 Predictions:", top_3_predictions)

    if detect_unknown_disease(top_3_predictions):
        return JSONResponse(content={"message": "Unknown disease detected."})

    questions = confirm_disease_with_symptoms(top_3_predictions)
    return JSONResponse(content={"questions": questions})

class SymptomResponse(BaseModel):
    answers: Dict[str, str]  # symptom name -> '1' or '0' 

@router.post("/confirm_symptoms")
async def confirm_symptoms(data: SymptomResponse):
    print("Received Data:", data)
    
    confirmed_disease, severity = process_user_responses(data.answers)

    print("Confirmed Disease:", confirmed_disease)
    print("Estimated Severity:", severity)

    return {
        "disease": confirmed_disease,
        "severity": severity,
        "message": f"Disease: {confirmed_disease}, Severity: {severity}"
    }
