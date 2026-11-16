"use strict";

const form = document.getElementById("register-form");
const errorBox = document.getElementById("form-error");
const button = document.getElementById("submit-btn");
const loginInput = document.getElementById("login");
const passwordInput = document.getElementById("password");
const confirmInput = document.getElementById("password-confirm");

api("/api/auth/me")
  .then(() => window.location.replace("/"))
  .catch(() => {});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError(errorBox);

  const login = loginInput.value.trim();
  const password = passwordInput.value;

  if (login.length < 3) {
    showError(errorBox, { message: "Логин должен быть не короче 3 символов" });
    return;
  }
  if (password.length < 6) {
    showError(errorBox, { message: "Пароль должен быть не короче 6 символов" });
    return;
  }
  if (password !== confirmInput.value) {
    showError(errorBox, { message: "Пароли не совпадают" });
    return;
  }

  button.disabled = true;

  try {
    await api("/api/auth/register", {
      method: "POST",
      body: { login: login, password: password },
    });
    window.location.replace("/");
  } catch (error) {
    showError(errorBox, error);
    button.disabled = false;
  }
});
