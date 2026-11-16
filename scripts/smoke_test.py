import json
import sys
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from urllib.parse import quote

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
PASSWORD = "secret123"

failures = 0


def parse(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


class Client:

    def __init__(self):
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar())
        )

    def request(self, method, path, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        url = BASE + quote(path, safe="/?=&")
        request = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")

        try:
            with self.opener.open(request, timeout=15) as response:
                return response.status, parse(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return error.code, parse(error.read().decode("utf-8"))


def check(name, condition, extra=""):
    global failures
    if condition:
        print("[ OK ] " + name)
    else:
        failures += 1
        print("[FAIL] " + name, extra)


def main():
    suffix = str(int(time.time()))[-6:]
    login_a = "alice" + suffix
    login_b = "bob" + suffix

    anon = Client()

    status, _ = anon.request("GET", "/api/books")
    check("GET /api/books без входа -> 401", status == 401, status)

    status, _ = anon.request("GET", "/api/auth/me")
    check("GET /api/auth/me без входа -> 401", status == 401, status)

    status, _ = anon.request("GET", "/")
    check("GET / -> 200", status == 200, status)

    status, _ = anon.request("GET", "/login")
    check("GET /login -> 200", status == 200, status)

    alice = Client()
    status, body = alice.request(
        "POST", "/api/auth/register", {"login": login_a, "password": PASSWORD}
    )
    check("POST /api/auth/register -> 201", status == 201, status)
    check("в ответе есть login", body and body.get("login") == login_a, body)
    check("в ответе нет password_hash", body and "password_hash" not in body)

    status, body = alice.request("GET", "/api/auth/me")
    check("GET /api/auth/me -> 200", status == 200 and body["login"] == login_a, body)

    status, _ = anon.request(
        "POST", "/api/auth/register", {"login": login_a, "password": PASSWORD}
    )
    check("повторный логин -> 400", status == 400, status)

    status, _ = anon.request(
        "POST", "/api/auth/register", {"login": "ab", "password": PASSWORD}
    )
    check("короткий логин -> 422", status == 422, status)

    status, _ = anon.request(
        "POST", "/api/auth/register", {"login": "user" + suffix, "password": "123"}
    )
    check("короткий пароль -> 422", status == 422, status)

    status, roman = alice.request("POST", "/api/genres", {"name": "Роман"})
    check("POST /api/genres -> 201", status == 201, status)

    status, fantasy = alice.request("POST", "/api/genres", {"name": "Фантастика"})
    check("второй жанр -> 201", status == 201, status)

    status, _ = alice.request("POST", "/api/genres", {"name": "Роман"})
    check("повторный жанр -> 400", status == 400, status)

    status, body = alice.request("GET", "/api/genres")
    check("GET /api/genres -> 2 жанра", status == 200 and len(body) == 2, body)

    status, book1 = alice.request(
        "POST",
        "/api/books",
        {
            "title": "Мастер и Маргарита",
            "author": "Михаил Булгаков",
            "year": 1967,
            "rating": 5,
            "is_read": True,
            "finished_at": "2024-05-12",
            "genre_id": roman["id"],
        },
    )
    check("POST /api/books -> 201", status == 201, status)
    check("is_read сохранился", book1["is_read"] is True, book1)
    check("дата прочтения сохранилась", book1["finished_at"] == "2024-05-12", book1)
    check("в ответе нет поля pages", "pages" not in book1, book1)

    status, book2 = alice.request(
        "POST",
        "/api/books",
        {"title": "Дюна", "author": "Фрэнк Герберт", "year": 1965,
         "genre_id": fantasy["id"]},
    )
    check("вторая книга -> 201", status == 201, status)
    check("is_read по умолчанию false", book2["is_read"] is False, book2)

    status, book3 = alice.request(
        "POST",
        "/api/books",
        {"title": "Солярис", "author": "Станислав Лем", "year": 1961,
         "rating": 4.5, "genre_id": fantasy["id"]},
    )
    check("третья книга -> 201", status == 201, status)

    status, book4 = alice.request(
        "POST",
        "/api/books",
        {"title": "Хоббит", "author": "Джон Толкин", "year": 1937,
         "rating": 4, "is_read": True},
    )
    check("четвёртая книга -> 201", status == 201, status)

    status, _ = alice.request("POST", "/api/books", {"title": "", "author": "Автор"})
    check("пустое название -> 422", status == 422, status)

    status, _ = alice.request(
        "POST", "/api/books", {"title": "Тест", "author": "Автор", "rating": 9}
    )
    check("оценка больше 5 -> 422", status == 422, status)

    status, _ = alice.request(
        "POST", "/api/books", {"title": "Тест", "author": "Автор", "genre_id": 999999}
    )
    check("несуществующий жанр -> 400", status == 400, status)

    status, body = alice.request("GET", "/api/books")
    check("список: total = 4", status == 200 and body["total"] == 4, body)
    check("список: 4 записи", len(body["items"]) == 4, body["items"])

    status, body = alice.request("GET", "/api/books?limit=2")
    check("limit=2 -> 2 записи", len(body["items"]) == 2 and body["total"] == 4, body)

    status, body = alice.request("GET", "/api/books?limit=2&offset=2")
    check("offset=2 -> ещё 2 записи", len(body["items"]) == 2, body)

    status, body = alice.request("GET", "/api/books?search=мастер")
    check("поиск по названию без учёта регистра", body["total"] == 1, body)

    status, body = alice.request("GET", "/api/books?search=лем")
    check("поиск по автору без учёта регистра", body["total"] == 1, body)

    status, body = alice.request("GET", "/api/books?is_read=true")
    check("фильтр is_read=true -> 2", body["total"] == 2, body)

    status, body = alice.request("GET", "/api/books?genre_id=" + str(fantasy["id"]))
    check("фильтр по жанру -> 2", body["total"] == 2, body)

    status, body = alice.request("GET", "/api/books?sort=year&order=asc")
    check("сортировка по году", body["items"][0]["year"] == 1937, body["items"][0])

    status, body = alice.request("GET", "/api/books?sort=rating&order=desc")
    check("сортировка по оценке", body["items"][0]["rating"] == 5.0, body["items"][0])

    status, _ = alice.request("GET", "/api/books?sort=bad")
    check("неизвестное поле сортировки -> 422", status == 422, status)

    status, body = alice.request("GET", "/api/books/" + str(book1["id"]))
    check("GET одной книги -> 200", status == 200 and body["id"] == book1["id"], body)

    status, body = alice.request(
        "PATCH",
        "/api/books/" + str(book1["id"]),
        {"title": "Мастер и Маргарита (роман)", "rating": 4.5},
    )
    check("PATCH книги -> 200", status == 200, status)
    check(
        "PATCH изменил поля",
        body["title"].endswith("(роман)") and body["rating"] == 4.5,
        body,
    )

    status, _ = alice.request(
        "PATCH", "/api/books/" + str(book1["id"]), {"rating": 9}
    )
    check("PATCH с оценкой 9 -> 422", status == 422, status)

    status, body = alice.request("GET", "/api/stats")
    check("GET /api/stats -> 200", status == 200, status)
    check("статистика: всего 4", body["total"] == 4, body)
    check("статистика: прочитано 2", body["read"] == 2, body)
    check("статистика: сумма оценок 13", abs(body["sum_rating"] - 13) < 0.01, body)
    check(
        "статистика: средняя оценка 4.33",
        abs(body["average_rating"] - 4.33) < 0.01,
        body,
    )
    check(
        "статистика: группировка по жанрам",
        len(body["by_genre"]) == 3,
        body["by_genre"],
    )

    bob = Client()
    status, _ = bob.request(
        "POST", "/api/auth/register", {"login": login_b, "password": PASSWORD}
    )
    check("регистрация второго пользователя -> 201", status == 201, status)

    status, body = bob.request("GET", "/api/books")
    check("второй пользователь видит 0 книг", body["total"] == 0, body)

    status, body = bob.request("GET", "/api/genres")
    check("у второго пользователя нет жанров", body == [], body)

    status, _ = bob.request("GET", "/api/books/" + str(book1["id"]))
    check("чужая книга -> 404", status == 404, status)

    status, _ = bob.request(
        "PATCH", "/api/books/" + str(book1["id"]), {"title": "Взлом"}
    )
    check("PATCH чужой книги -> 404", status == 404, status)

    status, _ = bob.request("DELETE", "/api/books/" + str(book1["id"]))
    check("DELETE чужой книги -> 404", status == 404, status)

    status, _ = bob.request("DELETE", "/api/genres/" + str(roman["id"]))
    check("DELETE чужого жанра -> 404", status == 404, status)

    status, _ = bob.request(
        "POST",
        "/api/books",
        {"title": "Чужая", "author": "Боб", "genre_id": roman["id"]},
    )
    check("книга с чужим жанром -> 400", status == 400, status)

    status, _ = bob.request(
        "POST", "/api/books", {"title": "Своя книга", "author": "Боб"}
    )
    check("второй пользователь создаёт книгу -> 201", status == 201, status)

    status, _ = alice.request("DELETE", "/api/books/" + str(book3["id"]))
    check("DELETE своей книги -> 204", status == 204, status)

    status, _ = alice.request("GET", "/api/books/" + str(book3["id"]))
    check("удалённая книга -> 404", status == 404, status)

    status, _ = alice.request("DELETE", "/api/genres/" + str(fantasy["id"]))
    check("DELETE своего жанра -> 204", status == 204, status)

    status, body = alice.request("GET", "/api/books?limit=100")
    check(
        "у книг удалённого жанра genre_id = null",
        all(item["genre_id"] != fantasy["id"] for item in body["items"]),
        body["items"],
    )

    status, _ = alice.request("POST", "/api/auth/logout")
    check("POST /api/auth/logout -> 204", status == 204, status)

    status, _ = alice.request("GET", "/api/books")
    check("после выхода -> 401", status == 401, status)

    status, _ = alice.request(
        "POST", "/api/auth/login", {"login": login_a, "password": "wrong-pass"}
    )
    check("неверный пароль -> 401", status == 401, status)

    status, _ = alice.request(
        "POST", "/api/auth/login", {"login": login_a, "password": PASSWORD}
    )
    check("вход с верным паролем -> 200", status == 200, status)

    status, body = alice.request("GET", "/api/books")
    check("после входа книги доступны", status == 200 and body["total"] == 3, body)

    print()
    if failures:
        print("Провалено проверок:", failures)
        return 1

    print("Все проверки пройдены")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
