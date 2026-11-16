"use strict";

const LIMIT = 5;

let offset = 0;
let total = 0;
let editingId = null;
let genres = [];
let books = {};
let searchTimer = null;

const byId = (id) => document.getElementById(id);

async function loadGenres() {
  try {
    genres = await api("/api/genres");
    renderGenres();
  } catch (error) {
    showError(byId("genre-error"), error);
  }
}

async function loadStats() {
  hideError(byId("stats-error"));

  try {
    const stats = await api("/api/stats");

    byId("stat-total").textContent = stats.total;
    byId("stat-read").textContent = stats.read;
    byId("stat-sum").textContent = stats.sum_rating;
    byId("stat-rating").textContent =
      stats.average_rating === null ? "—" : stats.average_rating;

    const list = byId("genre-stats");
    list.replaceChildren();

    stats.by_genre.forEach((row) => {
      const item = document.createElement("li");
      let text = row.name + ": " + row.books + " кн.";
      if (row.average_rating !== null) {
        text += ", средняя оценка " + row.average_rating;
      }
      item.textContent = text;
      list.appendChild(item);
    });
  } catch (error) {
    showError(byId("stats-error"), error);
  }
}

async function loadBooks(reset) {
  const status = byId("list-status");
  hideError(byId("list-error"));

  if (reset) {
    offset = 0;
    byId("book-list").replaceChildren();
  }

  status.textContent = "Загрузка...";

  const params = new URLSearchParams();
  const search = byId("search").value.trim();
  if (search) params.set("search", search);
  if (byId("filter-genre").value) params.set("genre_id", byId("filter-genre").value);
  if (byId("filter-read").value) params.set("is_read", byId("filter-read").value);

  const parts = byId("filter-sort").value.split(":");
  params.set("sort", parts[0]);
  params.set("order", parts[1]);
  params.set("limit", LIMIT);
  params.set("offset", offset);

  try {
    const data = await api("/api/books?" + params.toString());

    total = data.total;
    offset = offset + data.items.length;
    data.items.forEach(addBook);

    showListStatus();
  } catch (error) {
    status.textContent = "";
    showError(byId("list-error"), error);
  }
}

function showListStatus() {
  const status = byId("list-status");

  if (total === 0) {
    status.textContent = "Книг пока нет";
  } else {
    status.textContent = "Показано " + offset + " из " + total;
  }

  byId("more-btn").hidden = offset >= total;
}

function addBook(book) {
  books[book.id] = book;

  const item = document.createElement("li");
  item.className = "book";

  const info = document.createElement("div");
  info.className = "book-info";

  const title = document.createElement("h3");
  title.textContent = book.title;
  info.appendChild(title);

  const details = [book.author];
  if (book.year) details.push(book.year + " г.");

  const genre = genres.find((row) => row.id === book.genre_id);
  if (genre) details.push(genre.name);

  const meta = document.createElement("p");
  meta.className = "muted";
  meta.textContent = details.join(" · ");
  info.appendChild(meta);

  const badges = document.createElement("p");
  badges.className = "badges";

  if (book.rating !== null) {
    const rating = document.createElement("span");
    rating.className = "badge";
    rating.textContent = "Оценка: " + book.rating;
    badges.appendChild(rating);
  }

  const read = document.createElement("span");
  read.className = book.is_read ? "badge badge-read" : "badge badge-muted";
  read.textContent = book.is_read ? "Прочитана" : "Не прочитана";
  badges.appendChild(read);

  if (book.finished_at) {
    const date = document.createElement("span");
    date.className = "badge badge-muted";
    date.textContent = "Дата: " + book.finished_at;
    badges.appendChild(date);
  }

  info.appendChild(badges);

  const actions = document.createElement("div");
  actions.className = "book-actions";

  const edit = document.createElement("button");
  edit.type = "button";
  edit.className = "btn btn-light";
  edit.dataset.action = "edit";
  edit.dataset.id = book.id;
  edit.textContent = "Изменить";

  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "btn btn-light";
  remove.dataset.action = "delete";
  remove.dataset.id = book.id;
  remove.textContent = "Удалить";

  actions.append(edit, remove);

  item.append(info, actions);
  byId("book-list").appendChild(item);
}

function renderGenres() {
  const list = byId("genre-list");
  list.replaceChildren();

  genres.forEach((genre) => {
    const item = document.createElement("li");

    const name = document.createElement("span");
    name.textContent = genre.name;

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "btn-link";
    remove.dataset.action = "delete-genre";
    remove.dataset.id = genre.id;
    remove.title = "Удалить жанр";
    remove.textContent = "×";

    item.append(name, remove);
    list.appendChild(item);
  });

  byId("genres-empty").hidden = genres.length > 0;

  fillSelect("book-genre", "Без жанра");
  fillSelect("filter-genre", "Все жанры");
}

function fillSelect(id, emptyText) {
  const select = byId(id);
  const previous = select.value;

  select.replaceChildren();

  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = emptyText;
  select.appendChild(empty);

  genres.forEach((genre) => {
    const option = document.createElement("option");
    option.value = genre.id;
    option.textContent = genre.name;
    select.appendChild(option);
  });

  select.value = previous;
}

async function saveBook(event) {
  event.preventDefault();
  hideError(byId("form-error"));

  const body = {
    title: byId("book-title").value.trim(),
    author: byId("book-author").value.trim(),
    year: byId("book-year").value ? Number(byId("book-year").value) : null,
    rating: byId("book-rating").value ? Number(byId("book-rating").value) : null,
    is_read: byId("book-is-read").checked,
    finished_at: byId("book-finished").value || null,
    genre_id: byId("book-genre").value ? Number(byId("book-genre").value) : null,
  };

  byId("save-btn").disabled = true;

  try {
    if (editingId === null) {
      await api("/api/books", { method: "POST", body: body });
    } else {
      await api("/api/books/" + editingId, { method: "PATCH", body: body });
    }

    resetForm();
    await loadBooks(true);
    await loadStats();
  } catch (error) {
    showError(byId("form-error"), error);
  } finally {
    byId("save-btn").disabled = false;
  }
}

function startEdit(book) {
  editingId = book.id;

  byId("book-title").value = book.title;
  byId("book-author").value = book.author;
  byId("book-year").value = book.year === null ? "" : book.year;
  byId("book-rating").value = book.rating === null ? "" : book.rating;
  byId("book-is-read").checked = book.is_read;
  byId("book-finished").value = book.finished_at || "";
  byId("book-genre").value = book.genre_id === null ? "" : String(book.genre_id);

  byId("form-title").textContent = "Редактировать книгу";
  byId("cancel-btn").hidden = false;
  hideError(byId("form-error"));
  byId("book-form").scrollIntoView({ behavior: "smooth" });
}

function resetForm() {
  editingId = null;
  byId("book-form").reset();
  byId("form-title").textContent = "Добавить книгу";
  byId("cancel-btn").hidden = true;
  hideError(byId("form-error"));
}

async function onBookClick(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const book = books[button.dataset.id];
  if (!book) return;

  if (button.dataset.action === "edit") {
    startEdit(book);
    return;
  }

  if (!window.confirm("Удалить книгу «" + book.title + "»?")) return;

  try {
    await api("/api/books/" + book.id, { method: "DELETE" });
    if (editingId === book.id) resetForm();
    await loadBooks(true);
    await loadStats();
  } catch (error) {
    showError(byId("list-error"), error);
  }
}

async function saveGenre(event) {
  event.preventDefault();
  hideError(byId("genre-error"));

  const input = byId("genre-name");
  const name = input.value.trim();
  if (!name) return;

  try {
    await api("/api/genres", { method: "POST", body: { name: name } });
    input.value = "";
    await loadGenres();
  } catch (error) {
    showError(byId("genre-error"), error);
  }
}

async function onGenreClick(event) {
  const button = event.target.closest("button[data-action='delete-genre']");
  if (!button) return;

  const genre = genres.find((row) => row.id === Number(button.dataset.id));
  if (!genre) return;

  const question = "Удалить жанр «" + genre.name + "»? Книги останутся без жанра.";
  if (!window.confirm(question)) return;

  try {
    await api("/api/genres/" + genre.id, { method: "DELETE" });
    await loadGenres();
    await loadBooks(true);
    await loadStats();
  } catch (error) {
    showError(byId("genre-error"), error);
  }
}

function bindEvents() {
  byId("book-form").addEventListener("submit", saveBook);
  byId("cancel-btn").addEventListener("click", resetForm);
  byId("genre-form").addEventListener("submit", saveGenre);
  byId("book-list").addEventListener("click", onBookClick);
  byId("genre-list").addEventListener("click", onGenreClick);

  byId("search").addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadBooks(true), 300);
  });

  byId("filter-genre").addEventListener("change", () => loadBooks(true));
  byId("filter-read").addEventListener("change", () => loadBooks(true));
  byId("filter-sort").addEventListener("change", () => loadBooks(true));
  byId("more-btn").addEventListener("click", () => loadBooks(false));

  byId("logout-btn").addEventListener("click", async () => {
    try {
      await api("/api/auth/logout", { method: "POST" });
    } catch (error) {
    }
    window.location.replace("/login");
  });
}

async function init() {
  bindEvents();

  try {
    const me = await api("/api/auth/me");
    byId("user-login").textContent = me.login;
  } catch (error) {
    if (error.status === 401) {
      window.location.replace("/login");
      return;
    }
    showError(byId("list-error"), error);
    return;
  }

  await loadGenres();
  await loadStats();
  await loadBooks(true);
}

init();
