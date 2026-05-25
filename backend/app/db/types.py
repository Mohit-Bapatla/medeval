import json
import uuid
from typing import Any

from sqlalchemy import CHAR, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.types import TypeDecorator

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - dependency is declared, this keeps imports defensive.
    Vector = None  # type: ignore[assignment]


class GUID(TypeDecorator[uuid.UUID]):
    """Platform-independent UUID storage."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(
        self, value: uuid.UUID | str | None, dialect: Any
    ) -> uuid.UUID | str | None:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value: uuid.UUID | str | None, dialect: Any) -> uuid.UUID | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class VectorType(TypeDecorator[list[float]]):
    """pgvector in PostgreSQL, JSON text fallback elsewhere."""

    impl = Text
    cache_ok = False

    def __init__(self, dimension: int) -> None:
        self.dimension = dimension
        super().__init__()

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql" and Vector is not None:
            return dialect.type_descriptor(Vector(self.dimension))
        return dialect.type_descriptor(Text())

    def process_bind_param(
        self, value: list[float] | None, dialect: Any
    ) -> list[float] | str | None:
        if value is None:
            return None
        if len(value) != self.dimension:
            raise ValueError(f"Expected vector dimension {self.dimension}, received {len(value)}")
        if dialect.name == "postgresql":
            return value
        return json.dumps([float(item) for item in value])

    def process_result_value(self, value: Any, dialect: Any) -> list[float] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return [float(item) for item in json.loads(value)]
        return [float(item) for item in value]
