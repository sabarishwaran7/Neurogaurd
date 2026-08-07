/* global fetch, localStorage, location, navigator, document */
(function () {
  const TOKEN_KEY = "aap_token";

  function formatDetail(detail) {
    if (!detail) return "Request failed";
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map(function (x) {
          return (x && (x.msg || x.message)) || JSON.stringify(x);
        })
        .join(", ");
    }
    if (typeof detail === "object") return JSON.stringify(detail);
    return String(detail);
  }

  async function api(path, options) {
    options = options || {};
    var method = options.method || "GET";
    var body = options.body;
    var auth = options.auth !== false;
    var rawBody = !!options.rawBody;
    var headers = Object.assign({}, options.headers || {});

    if (body && !rawBody && !(body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    var token = localStorage.getItem(TOKEN_KEY);
    if (auth && token) {
      headers["Authorization"] = "Bearer " + token;
    }

    var res = await fetch(path, {
      method: method,
      headers: headers,
      body: rawBody ? body : body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401 && auth) {
      localStorage.removeItem(TOKEN_KEY);
      var p = location.pathname || "";
      if (p !== "/login" && p !== "/register") {
        location.href = "/login";
      }
    }

    if (!res.ok) {
      var msg = await res.text();
      try {
        var j = JSON.parse(msg);
        msg = formatDetail(j.detail) || msg;
      } catch (e) {
        /* ignore */
      }
      throw new Error(msg || res.statusText);
    }

    if (res.status === 204) return null;
    var ct = res.headers.get("content-type") || "";
    if (ct.indexOf("application/json") !== -1) return res.json();
    return res.text();
  }

  function setToken(t) {
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
  }

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function requireAuth() {
    if (!getToken()) location.href = "/login";
  }

  function logout() {
    setToken(null);
    location.href = "/login";
  }

  function toast(msg, kind) {
    var el = document.getElementById("toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "toast";
      el.className = "toast";
      el.setAttribute("role", "status");
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.classList.remove("toast--success", "toast--error");
    if (kind === "error") el.classList.add("toast--error");
    else el.classList.add("toast--success");
    el.classList.add("show");
    clearTimeout(el._t);
    el._t = setTimeout(function () {
      el.classList.remove("show");
    }, 3400);
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast("Copied to clipboard", "ok");
    } catch (e) {
      toast("Copy failed — select and copy manually", "error");
    }
  }

  window.AAP = {
    api: api,
    setToken: setToken,
    getToken: getToken,
    requireAuth: requireAuth,
    logout: logout,
    toast: toast,
    copyText: copyText,
  };
})();
