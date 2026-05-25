import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.human_review import HumanReview
from app.models.model_response import ModelResponse
from app.schemas.human_reviews import HumanReviewCreate, HumanReviewRead

router = APIRouter(tags=["human-reviews"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/responses/{response_id}/human-review",
    response_model=HumanReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_human_review(
    response_id: uuid.UUID, payload: HumanReviewCreate, db: DbSession
) -> HumanReviewRead:
    if db.get(ModelResponse, response_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model response not found",
        )
    review = HumanReview(
        model_response_id=response_id,
        reviewer_name=payload.reviewer_name,
        reviewer_role=payload.reviewer_role,
        correctness_label=payload.correctness_label,
        groundedness_label=payload.groundedness_label,
        refusal_label=payload.refusal_label,
        notes=payload.notes,
        metadata_json=payload.metadata,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return serialize_human_review(review)


@router.get("/responses/{response_id}/human-reviews", response_model=list[HumanReviewRead])
def list_human_reviews(response_id: uuid.UUID, db: DbSession) -> list[HumanReviewRead]:
    if db.get(ModelResponse, response_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model response not found",
        )
    reviews = (
        db.execute(
            select(HumanReview)
            .where(HumanReview.model_response_id == response_id)
            .order_by(HumanReview.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [serialize_human_review(review) for review in reviews]


def serialize_human_review(review: HumanReview) -> HumanReviewRead:
    return HumanReviewRead(
        id=review.id,
        model_response_id=review.model_response_id,
        reviewer_name=review.reviewer_name,
        reviewer_role=review.reviewer_role,
        correctness_label=review.correctness_label,  # type: ignore[arg-type]
        groundedness_label=review.groundedness_label,  # type: ignore[arg-type]
        refusal_label=review.refusal_label,  # type: ignore[arg-type]
        notes=review.notes,
        metadata=review.metadata_json,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )
