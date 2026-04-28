// ch16 / step 1 — API 通信を 1 ファイルに集約。
//
// ゴール:
//   サーバとの会話は全部このファイルだけが担当。 React/Vue/Svelte に
//   移植するときも、 ここをそのまま import すれば済む。
//
// 使い方:
//   import { Api } from "./step1_api_module.js";
//   const api = new Api("http://localhost:8000", localStorage.getItem("token"));
//   const me  = await api.me();

export class Api {
  constructor(baseUrl, token = null) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  setToken(token) { this.token = token; }

  async _fetch(path, { method = "GET", body = null } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;

    const res = await fetch(this.baseUrl + path, {
      method,
      headers,
      body: body !== null ? JSON.stringify(body) : null,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || `HTTP ${res.status}`);
    }
    return data;
  }

  // ---------- public ----------
  register(name, password)   { return this._fetch("/api/register", { method: "POST", body: { name, password } }); }
  login(name, password)      { return this._fetch("/api/login",    { method: "POST", body: { name, password } }); }
  logout()                   { return this._fetch("/api/logout",   { method: "POST" }); }
  me()                       { return this._fetch("/api/me"); }
  gachaList()                { return this._fetch("/api/gacha/list"); }
  pull(gachaId)              { return this._fetch("/api/gacha/pull", { method: "POST", body: { gacha_id: gachaId } }); }
  box()                      { return this._fetch("/api/box"); }
  claimDaily()               { return this._fetch("/api/daily/claim", { method: "POST" }); }
}
