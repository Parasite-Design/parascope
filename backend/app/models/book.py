from typing import Optional

from pydantic import BaseModel


class BookBase(BaseModel):
    title: str
    author: str
    publication_year: int
    isbn: Optional[str] = None


class BookCreate(BookBase):
    pass


class BookResponse(BookBase):
    id: str
