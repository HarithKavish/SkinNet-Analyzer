from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import pytz  # For timezone handling
from contextlib import asynccontextmanager  # For lifespan event handler

router = APIRouter()

# Configure loggers
logging.basicConfig(level=logging.INFO)
user_logger = logging.getLogger("user_pings")
cron_logger = logging.getLogger("cron_pings")
startup_logger = logging.getLogger("startup_events")

# Set your local timezone (update to your timezone)
local_timezone = pytz.timezone("Asia/Kolkata")  # Example: change to your preferred timezone

# Deployment timestamp (frozen once at startup)
DEPLOYED_AT = datetime.now(local_timezone).strftime("%d-%m-%Y %I:%M %p")

@router.get("/status")
async def status(request: Request):
    current_time = datetime.now(local_timezone).strftime("%d-%m-%Y %I:%M %p")
    heartbeat = request.headers.get("X-Heartbeat", "false").lower() == "true"
    
    if heartbeat:
        cron_logger.info(f"Cronjob heartbeat ping at {current_time}")
    else:
        user_logger.info(f"User accessed /status at {current_time}")
    
    return JSONResponse(
        content={
            "status": "online",
            "deployed_at": DEPLOYED_AT,  # Deployment time, not now()
            "checked_at": current_time   # Ping check time
        },
        status_code=200
    )

# Lifespan event handler for startup
@asynccontextmanager
async def lifespan(app):
    startup_logger.info(f"Backend redeployed at {DEPLOYED_AT}")
    yield  # Startup is handled here; you could add shutdown handling here if needed.
