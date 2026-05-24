from pydantic import BaseModel, Field


class PageParams(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    cursor: str | None = None


class PageMeta(BaseModel):
    next_cursor: str | None = None
    total: int | None = None

