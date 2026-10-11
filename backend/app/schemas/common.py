from pydantic import BaseModel


class Message(BaseModel):
    message: str


class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int
