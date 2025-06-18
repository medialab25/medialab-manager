from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api", tags=["health"])

class HealthResponse(BaseModel):
    status: str
    timestamp: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    ) 