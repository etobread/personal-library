from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Book, Genre, User
from app.schemas import GenreStat, StatsOut

router = APIRouter(prefix="/api/stats", tags=["Статистика"])


@router.get("", response_model=StatsOut)
def get_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    own_books = Book.owner_id == user.id

    total = db.scalar(select(func.count(Book.id)).where(own_books)) or 0
    read = (
        db.scalar(
            select(func.count(Book.id)).where(own_books, Book.is_read.is_(True))
        )
        or 0
    )
    sum_rating = db.scalar(select(func.sum(Book.rating)).where(own_books)) or 0
    average_rating = db.scalar(select(func.avg(Book.rating)).where(own_books))

    rows = db.execute(
        select(Genre.name, func.count(Book.id), func.avg(Book.rating))
        .select_from(Genre)
        .join(Book, Book.genre_id == Genre.id)
        .where(Genre.owner_id == user.id)
        .group_by(Genre.id)
        .order_by(func.count(Book.id).desc())
    ).all()

    by_genre = [
        GenreStat(
            name=name,
            books=books,
            average_rating=round(rating, 2) if rating is not None else None,
        )
        for name, books, rating in rows
    ]

    without_genre = (
        db.scalar(
            select(func.count(Book.id)).where(own_books, Book.genre_id.is_(None))
        )
        or 0
    )
    if without_genre:
        by_genre.append(
            GenreStat(name="Без жанра", books=without_genre, average_rating=None)
        )

    return {
        "total": total,
        "read": read,
        "sum_rating": round(sum_rating, 2),
        "average_rating": round(average_rating, 2) if average_rating else None,
        "by_genre": by_genre,
    }
