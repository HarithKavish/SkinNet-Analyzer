import logging
import numpy as np
import cv2
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import pytz  # Import pytz for timezone management
from contextlib import asynccontextmanager  # For creating lifespan event handlers

from classify import ensemble_classify  # Your classification logic

# Configure loggers
logging.basicConfig(level=logging.INFO)

user_logger = logging.getLogger("ml_user_requests")
cron_logger = logging.getLogger("ml_cron_heartbeats")
startup_logger = logging.getLogger("ml_startup_events")

# FastAPI app initialization
app = FastAPI()

# Set your local timezone (replace with your desired timezone)
local_timezone = pytz.timezone("Asia/Kolkata")  # Change to your desired timezone if needed
# Deployment timestamp (frozen once at startup)
DEPLOYED_AT = datetime.now(local_timezone).strftime("%d-%m-%Y %I:%M %p")

@app.get("/")
async def health(request: Request):
    current_time = datetime.now(local_timezone).strftime("%d-%m-%Y %I:%M %p")
    heartbeat = request.headers.get("X-Heartbeat", "false").lower() == "true"

    if heartbeat:
        cron_logger.info(f"Cronjob heartbeat ping at {current_time}")
    else:
        user_logger.info(f"User accessed health check at {current_time}")

    return {"status": "ok", "deployed_at": DEPLOYED_AT, "checked_at": current_time}

@app.post("/")
async def predict(file: UploadFile = File(...)):
    try:
        user_logger.info(f"Prediction request received. File content type: {file.content_type}")

        # Validate file type
        if file.content_type not in ["image/jpeg", "image/png"]:
            user_logger.error(f"Invalid file type: {file.content_type}")
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
        user_logger.exception("Prediction failed.")
        raise HTTPException(status_code=500, detail=str(e))

# Use lifespan for startup event
@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_logger.info(f"ML API backend redeployed at {DEPLOYED_AT}")
    yield

# Assign the lifespan function to FastAPI's lifespan parameter
app.lifespan = lifespan

# To run using: uvicorn ml_backend:app --host 0.0.0.0 --port 7860
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
