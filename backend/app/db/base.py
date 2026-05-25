from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import Document, DocumentChunk, RetrievalQuery, RetrievalResult  # noqa: E402, F401
