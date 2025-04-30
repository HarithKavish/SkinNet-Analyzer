import logging
from logging.handlers import RotatingFileHandler
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from typing import Any

from apis.city_coordinates_api import get_city_coordinates
from apis.nearby_hospitals_api import get_nearby_hospitals
from apis.gemini_api import gemini

# Centralized logging setup
handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=5)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger = logging.getLogger("info_logger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

router = APIRouter()

# Pydantic model
class DiseaseRequest(BaseModel):
    disease: str
    severity: str
    location: str

@router.post("/get_disease_info")
async def get_disease_info(request: Request):
    try:
        body: dict[str, Any] = await request.json()
        try:
            data = DiseaseRequest(**body)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.errors()}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid request", "details": e.errors()}
            )

        if data.severity == "Out of Class":
            logger.info(f"Out of Class severity: {data.disease}")
            return {"out_of_class": True}

        logger.info(f"Processing: {data.disease} in {data.location}")

        query = (
            f"Provide detailed information about the skin disease name present in the title {data.disease} ignoring the title itself. Include:\n"
            "- External and internal symptoms (in bullet points)\n"
            "- Steps to take care of it\n"
        )

        print(data.location)

        try:
            ai_response = gemini(query).text
        except Exception as e:
            logger.exception(f"Gemini API failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch disease info")

        try:
            print(data.location)
            coords = get_city_coordinates(data.location)
            print(coords)
            hospitals = get_nearby_hospitals(coords)
            print(hospitals)
        except Exception:
            logger.exception("Nearby hospital fetch failed.")
            hospitals = []

        hospital_infos = [
            {
                "name": h.get("tags", {}).get("name", f"Hospital {i+1}"),
                "location": data.location,
                "maps_url": f"https://www.google.com/maps/search/?q={h['lat']},{h['lon']}"
            }
            for i, h in enumerate(hospitals)
        ]
        print(hospital_infos)

        return {
            "disease": data.disease,
            "severity": data.severity,
            "location": data.location,
            "symptoms_care": ai_response,
            "hospitals": hospital_infos,
        }

    except Exception:
        logger.exception("Unhandled exception.")
        raise HTTPException(status_code=500, detail="Internal server error")
