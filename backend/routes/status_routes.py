from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/status")
async def status():
    return JSONResponse(content={"status": "online","deployed_at": "03-05-2025 02:05 PM"}, status_code=200)
