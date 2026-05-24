from fastapi import APIRouter

from app.core.config import settings
from app.schemas.status import StatusResponse

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    return StatusResponse(
        name=settings.PROJECT_NAME,
        purpose="healthcare RAG evaluation",
        version=settings.VERSION,
        modules=[
            "documents",
            "datasets",
            "retrieval",
            "experiments",
            "evaluations",
            "reports",
        ],
    )
