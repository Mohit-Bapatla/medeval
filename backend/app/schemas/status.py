from pydantic import BaseModel


class StatusResponse(BaseModel):
    name: str
    purpose: str
    version: str
    modules: list[str]
