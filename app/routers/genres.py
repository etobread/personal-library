from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Book, Genre, User
from app.schemas import GenreIn, GenreOut

router = APIRouter(prefix="/api/genres", tags=["Жанры"])


@router.get("", response_model=list[GenreOut])
def get_genres(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        select(Genre)
        .where(Genre.owner_id == user.id)
        .order_by(Genre.name)
    )
    return db.scalars(query).all()


@router.post("", response_model=GenreOut, status_code=201)
def create_genre(
    data: GenreIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Название жанра не может быть пустым")

    exists = db.scalar(
        select(Genre).where(Genre.owner_id == user.id, Genre.name == name)
    )
    if exists is not None:
        raise HTTPException(status_code=400, detail="Такой жанр уже есть")

    genre = Genre(name=name, owner_id=user.id)
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre


@router.delete("/{genre_id}", status_code=204)
def delete_genre(
    genre_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    genre = db.scalar(
        select(Genre).where(Genre.id == genre_id, Genre.owner_id == user.id)
    )
    if genre is None:
        raise HTTPException(status_code=404, detail="Жанр не найден")

    db.execute(update(Book).where(Book.genre_id == genre.id).values(genre_id=None))
    db.delete(genre)
    db.commit()
    return Response(status_code=204)
