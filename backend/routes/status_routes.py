from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import os

router = APIRouter()

# Setup loggers (separate channels)
user_logger = logging.getLogger("user_pings")
cron_logger = logging.getLogger("cron_pings")
startup_logger = logging.getLogger("startup_events")

# Optional: configure handlers separately if needed

# Deployment timestamp - loaded once on startup
DEPLOYED_AT = datetime.now().strftime("%d-%m-%Y %I:%M %p")

@router.get("/status")
async def status(request: Request):
    current_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")
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

# Log server startup
@router.on_event("startup")
async def startup_event():
    startup_logger.info(f"Backend redeployed at {DEPLOYED_AT}")
