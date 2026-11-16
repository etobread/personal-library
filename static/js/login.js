"use strict";

const form = document.getElementById("login-form");
const errorBox = document.getElementById("form-error");
const button = document.getElementById("submit-btn");
const loginInput = document.getElementById("login");
const passwordInput = document.getElementById("password");

api("/api/auth/me")
  .then(() => window.location.replace("/"))
  .catch(() => {});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError(errorBox);
  button.disabled = true;

  try {
    await api("/api/auth/login", {
      method: "POST",
      body: {
        login: loginInput.value.trim(),
        password: passwordInput.value,
      },
    });
    window.location.replace("/");
  } catch (error) {
    showError(errorBox, error);
    button.disabled = false;
  }
});
