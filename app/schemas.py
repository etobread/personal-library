from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class RegisterIn(BaseModel):
    login: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=6, max_length=72)


class LoginIn(BaseModel):
    login: str = Field(min_length=1, max_length=30)
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    created_at: datetime


class GenreIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)


class GenreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=0, le=2100)
    rating: float | None = Field(default=None, ge=0, le=5)
    is_read: bool = False
    finished_at: date | None = None
    genre_id: int | None = None


class BookUpdate(BaseModel):

    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=0, le=2100)
    rating: float | None = Field(default=None, ge=0, le=5)
    is_read: bool | None = None
    finished_at: date | None = None
    genre_id: int | None = None


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    year: int | None
    rating: float | None
    is_read: bool
    finished_at: date | None
    genre_id: int | None
    created_at: datetime


class BookList(BaseModel):
    items: list[BookOut]
    total: int


class GenreStat(BaseModel):
    name: str
    books: int
    average_rating: float | None


class StatsOut(BaseModel):
    total: int
    read: int
    sum_rating: float
    average_rating: float | None
    by_genre: list[GenreStat]
