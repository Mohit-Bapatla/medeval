from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import (  # noqa: E402, F401
    Dataset,
    Document,
    DocumentChunk,
    EvaluationResult,
    EvidenceLink,
    Experiment,
    ModelResponse,
    PromptTemplate,
    QAExample,
    ResponseRetrievedChunk,
    RetrievalQuery,
    RetrievalResult,
)
