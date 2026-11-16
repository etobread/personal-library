Личная библиотека — учебная практика

Веб-приложение для учёта личной библиотеки: пользователь регистрируется по логину,
добавляет книги и жанры и видит **только свои** записи.

ФИО: Тимофеев Артём Сергеевич
Группа: ИСиП 1-9-24
Вариант: 1

Что умеет

регистрация, вход, выход, `GET /api/auth/me`;
пароль хранится в виде bcrypt-хеша, сессия — в подписанной cookie;
книги: список, одна книга, создание, изменение (`PATCH`), удаление;
жанры: список, создание, удаление;
поиск по названию и автору (`ilike`), фильтры по жанру и по признаку «прочитана»;
сортировка по названию, автору, году и оценке;
пагинация через `limit` / `offset` (на странице кнопка «Показать ещё»);
статистика: `count`, `sum`, `avg` и `group_by` по жанрам;
страницы входа, регистрации и главная; есть состояния «загрузка», «пусто» и
  сообщения об ошибках (401, 404, 422);
автодокументация Swagger: `/docs`.

Стек: FastAPI, SQLAlchemy 2, Alembic, Pydantic, SQLite, bcrypt,
`SessionMiddleware`, HTML + CSS + JavaScript (fetch).

Запуск

#Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env

python -c "import secrets; print(secrets.token_urlsafe(32))"

alembic upgrade head
uvicorn app.main:app --reload
```

Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"

alembic upgrade head
uvicorn app.main:app --reload
```

Файл `.env`
`SECRET_KEY` - ключ подписи cookie-сессии (обязателен)

`DATABASE_URL` - строка подключения к БД

Структура проекта

```text
app/
├── main.py          создание приложения, middleware, статические страницы
├── config.py        настройки из .env
├── database.py      engine, сессии, Base, get_db
├── models.py        таблицы User, Genre, Book
├── schemas.py       схемы Pydantic
├── security.py      хеширование паролей
├── deps.py          get_current_user
└── routers/
    ├── auth.py      регистрация, вход, выход, /me
    ├── books.py     CRUD книг, поиск, фильтры, пагинация
    ├── genres.py    список, создание и удаление жанров
    └── stats.py     статистика
migrations/          миграции Alembic
static/              html, css, js
scripts/             smoke_test.py
```