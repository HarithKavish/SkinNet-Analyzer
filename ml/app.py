import logging
import numpy as np
import cv2
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from classify import ensemble_classify  # Your classification logic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI()

@app.get("/")
async def health():
    return {"status": "ok","deployed_at": "03-05-2025 07:45 PM"}

@app.post("/")
async def predict(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file with content type: {file.content_type}")

        # Validate file type
        if file.content_type not in ["image/jpeg", "image/png"]:
            logger.error(f"Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPEG or PNG image.")

        image_bytes = await file.read()

        # Convert bytes to PIL Image
        img = Image.fromarray(
            cv2.cvtColor(cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        )

        # Run model prediction
        top_3_predictions = ensemble_classify(img)

        return JSONResponse(content={"predictions": top_3_predictions})

    except Exception as e:
        logger.exception("Prediction failed.")
        raise HTTPException(status_code=500, detail=str(e))

# To run using: uvicorn ml_backend:app --host 0.0.0.0 --port 7860
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

# A new change made 1