from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginIn, RegisterIn, UserOut
from app.security import check_password, hash_password

router = APIRouter(prefix="/api/auth", tags=["Авторизация"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    login = data.login.strip()
    if not login:
        raise HTTPException(status_code=400, detail="Логин не может быть пустым")

    if db.scalar(select(User).where(User.login == login)) is not None:
        raise HTTPException(status_code=400, detail="Такой логин уже занят")

    user = User(login=login, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    return user


@router.post("/login", response_model=UserOut)
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.login == data.login.strip()))
    if user is None or not check_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    request.session["user_id"] = user.id
    return user


@router.post("/logout", status_code=204)
def logout(request: Request):
    request.session.clear()
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
