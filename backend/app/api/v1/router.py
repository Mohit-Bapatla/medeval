from fastapi import APIRouter

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.documents import router as documents_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.prompts import router as prompts_router
from app.api.v1.qa_examples import router as qa_examples_router
from app.api.v1.rag import router as rag_router
from app.api.v1.reports import router as reports_router
from app.api.v1.retrieval import router as retrieval_router
from app.api.v1.status import router as status_router

api_router = APIRouter()
api_router.include_router(status_router)
api_router.include_router(documents_router)
api_router.include_router(retrieval_router)
api_router.include_router(datasets_router)
api_router.include_router(qa_examples_router)
api_router.include_router(prompts_router)
api_router.include_router(rag_router)
api_router.include_router(evaluations_router)
api_router.include_router(experiments_router)
api_router.include_router(dashboard_router)
api_router.include_router(reports_router)
