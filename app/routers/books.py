from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Book, Genre, User
from app.schemas import BookIn, BookList, BookOut, BookUpdate

router = APIRouter(prefix="/api/books", tags=["Книги"])

SORT_FIELDS = {
    "title": Book.title,
    "author": Book.author,
    "year": Book.year,
    "rating": Book.rating,
}


def find_book(db: Session, book_id: int, user_id: int) -> Book:
    book = db.scalar(
        select(Book).where(Book.id == book_id, Book.owner_id == user_id)
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book


def check_genre(db: Session, genre_id: Optional[int], user_id: int) -> None:
    if genre_id is None:
        return

    genre = db.scalar(
        select(Genre).where(Genre.id == genre_id, Genre.owner_id == user_id)
    )
    if genre is None:
        raise HTTPException(status_code=400, detail="Жанр не найден")


@router.get("", response_model=BookList)
def get_books(
    search: Optional[str] = None,
    genre_id: Optional[int] = None,
    is_read: Optional[bool] = None,
    sort: Literal["title", "author", "year", "rating"] = "title",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Book).where(Book.owner_id == user.id)

    if search:
        text = f"%{search.strip()}%"
        query = query.where(or_(Book.title.ilike(text), Book.author.ilike(text)))

    if genre_id is not None:
        query = query.where(Book.genre_id == genre_id)

    if is_read is not None:
        query = query.where(Book.is_read == is_read)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    column = SORT_FIELDS[sort]
    if order == "desc":
        query = query.order_by(column.desc())
    else:
        query = query.order_by(column.asc())

    books = db.scalars(query.limit(limit).offset(offset)).all()
    return {"items": books, "total": total}


@router.get("/{book_id}", response_model=BookOut)
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return find_book(db, book_id, user.id)


@router.post("", response_model=BookOut, status_code=201)
def create_book(
    data: BookIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_genre(db, data.genre_id, user.id)

    book = Book(**data.model_dump(), owner_id=user.id)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@router.patch("/{book_id}", response_model=BookOut)
def update_book(
    book_id: int,
    data: BookUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = find_book(db, book_id, user.id)

    changes = data.model_dump(exclude_unset=True)

    for field in ("title", "author"):
        if field in changes and not changes[field]:
            raise HTTPException(
                status_code=422, detail="Название и автор не могут быть пустыми"
            )

    if "genre_id" in changes:
        check_genre(db, changes["genre_id"], user.id)

    for field, value in changes.items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = find_book(db, book_id, user.id)
    db.delete(book)
    db.commit()
    return Response(status_code=204)
