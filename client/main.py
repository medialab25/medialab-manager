from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Client Service")

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    ) 