import datetime
from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter()

@router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
