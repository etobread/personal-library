"use strict";

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function errorText(data, status) {
  if (data && typeof data.detail === "string") {
    return data.detail;
  }
  if (data && Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join("; ");
  }
  if (status === 401) return "Нужно войти в систему";
  if (status === 404) return "Запись не найдена";
  if (status === 422) return "Проверьте заполнение полей";
  return "Ошибка запроса (" + status + ")";
}

async function api(url, options = {}) {
  const config = {
    method: options.method || "GET",
    credentials: "same-origin",
    headers: {},
  };

  if (options.body !== undefined) {
    config.headers["Content-Type"] = "application/json";
    config.body = JSON.stringify(options.body);
  }

  let response;
  try {
    response = await fetch(url, config);
  } catch (error) {
    throw new ApiError(0, "Сервер недоступен, проверьте, что запущен uvicorn");
  }

  if (response.status === 204) {
    return null;
  }

  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (error) {
    data = null;
  }

  if (!response.ok) {
    throw new ApiError(response.status, errorText(data, response.status));
  }
  return data;
}

function showError(box, error) {
  if (error.status === 401) {
    window.location.replace("/login");
    return;
  }
  box.textContent = error.message;
  box.hidden = false;
}

function hideError(box) {
  box.textContent = "";
  box.hidden = true;
}
