// gacha_gacha 学習モードフロント
// =============================================================================
// 通常モード (期待形式の応答が返ってくる) では普通のガチャUIが動き、
// サーバの応答が期待形式から外れたら、生のJSONを画面+デバッグコンソールに見せる。
// = サイレント失敗しないことで、学習者が「サーバから何が返っているか」を観察できる。

const $ = (id) => document.getElementById(id);

// ---- API base URL の管理 -----------------------------------------------------
const API = {
  base: (() => {
    try { return localStorage.getItem("gg_api_base") || "http://localhost:8000"; }
    catch { return "http://localhost:8000"; }
  })(),
  // Bearer Token (= login/register成功時にサーバから受け取る短いランダム文字列)
  // ページをリロードしても残るよう localStorage に保存する。
  token: (() => {
    try { return localStorage.getItem("gg_token") || null; } catch { return null; }
  })(),
};
$("api-base-input").value = API.base;
$("api-base-input").addEventListener("change", (e) => {
  API.base = e.target.value.trim().replace(/\/+$/, "");
  try { localStorage.setItem("gg_api_base", API.base); } catch {}
  setStatus("idle");
});

function setToken(t) {
  API.token = t || null;
  try {
    if (t) localStorage.setItem("gg_token", t);
    else   localStorage.removeItem("gg_token");
  } catch {}
}

// ---- ステータスインジケータ --------------------------------------------------
function setStatus(s) {
  const el = $("api-status");
  el.className = "api-status " + s;
  el.title = {
    idle:    "未確認",
    ok:      "サーバが応答した",
    fail:    "サーバ未応答 / ネットワーク失敗",
    partial: "応答はあるが期待形式と違う",
  }[s];
}

// ---- shape チェック ----------------------------------------------------------
//   "*" → 何でも OK
//   "string"/"number"/"boolean"/"object"/"array" → typeof 一致
//   "?T" → null 許容 (例: "?number")
//   オブジェクト → 各キーを再帰チェック (余分なキーは許す)
//   配列 [<T>] → 各要素が <T> 形式
function checkShape(value, expected, path = "") {
  if (expected === "*" || expected == null) return [];
  if (typeof expected === "string") {
    if (expected.startsWith("?") && value == null) return [];
    const t = expected.replace(/^\?/, "");
    if (t === "array")   return Array.isArray(value) ? [] : [{path, want: t, got: type(value)}];
    if (t === "object")  return (typeof value === "object" && !Array.isArray(value) && value != null)
                                 ? [] : [{path, want: t, got: type(value)}];
    return typeof value === t ? [] : [{path, want: t, got: type(value)}];
  }
  if (Array.isArray(expected)) {
    if (!Array.isArray(value)) return [{path, want: "array", got: type(value)}];
    if (expected.length === 0) return [];
    const errs = [];
    for (let i = 0; i < value.length; i++) {
      errs.push(...checkShape(value[i], expected[0], `${path}[${i}]`));
    }
    return errs;
  }
  if (typeof expected === "object") {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      return [{path, want: "object", got: type(value)}];
    }
    const errs = [];
    for (const k of Object.keys(expected)) {
      errs.push(...checkShape(value[k], expected[k], path ? `${path}.${k}` : k));
    }
    return errs;
  }
  return [];
}
function type(v) {
  if (v === null) return "null";
  if (Array.isArray(v)) return "array";
  return typeof v;
}

// ---- フェッチ + 全往復をデバッグコンソールに記録 -----------------------------
async function call(method, path, { body, expect } = {}) {
  const start = performance.now();
  const url = API.base + path;
  // file:// + クロスオリジン fetch を素直に通すため credentials は使わない。
  // 認証は Authorization: Bearer <token> ヘッダで送る。
  const init = { method, credentials: "omit", headers: {} };
  if (body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  if (API.token) {
    init.headers["Authorization"] = `Bearer ${API.token}`;
  }
  const result = { method, path, url, body, ts: new Date(), expect };

  try {
    const res = await fetch(url, init);
    result.status = res.status;
    const text = await res.text();
    result.rawText = text;
    try { result.json = JSON.parse(text); }
    catch { result.json = null; }
  } catch (e) {
    result.networkError = e.message;
  }
  result.elapsedMs = Math.round(performance.now() - start);

  // shape チェック
  if (expect && result.json != null) {
    result.shapeErrors = checkShape(result.json, expect);
    result.shapeOk = result.shapeErrors.length === 0;
  }
  // ステータスインジケータ更新
  if (result.networkError) setStatus("fail");
  else if (result.shapeErrors && !result.shapeOk) setStatus("partial");
  else if (result.status >= 200 && result.status < 300) setStatus("ok");
  else setStatus("partial");

  appendDebug(result);
  return result;
}

// ---- デバッグコンソール ------------------------------------------------------
const _debugEntries = [];
function appendDebug(r) {
  _debugEntries.unshift(r);
  if (_debugEntries.length > 30) _debugEntries.length = 30;
  renderDebug();
}
$("debug-clear").addEventListener("click", () => {
  _debugEntries.length = 0;
  renderDebug();
});

function renderDebug() {
  const log = $("debug-log");
  if (_debugEntries.length === 0) {
    log.innerHTML = `<p class="debug-empty">まだリクエストが投げられていません。 上のフォームから何かしてみてください。</p>`;
    return;
  }
  log.innerHTML = "";
  for (const e of _debugEntries) {
    log.appendChild(renderEntry(e));
  }
}

function renderEntry(e) {
  const el = document.createElement("div");
  el.className = "debug-entry";

  // ステータスのクラス
  let statusCls = "serr", statusText = "—";
  if (e.networkError) {
    statusCls = "serr"; statusText = "NETWORK";
  } else if (e.status) {
    statusText = String(e.status);
    statusCls = e.status >= 500 ? "s5xx"
              : e.status >= 400 ? "s4xx"
              : e.status >= 200 ? "s2xx" : "serr";
  }

  // shape インジケータ
  let shapeHtml = "";
  if (e.expect && !e.networkError) {
    if (e.shapeOk) shapeHtml = `<span class="shape match">✓ 期待形式</span>`;
    else shapeHtml = `<span class="shape mismatch">✗ 期待形式と違う (${e.shapeErrors.length}箇所)</span>`;
  }

  const t = e.ts;
  const hh = String(t.getHours()).padStart(2, "0");
  const mm = String(t.getMinutes()).padStart(2, "0");
  const ss = String(t.getSeconds()).padStart(2, "0");

  el.innerHTML = `
    <div class="row1">
      <span class="ts">${hh}:${mm}:${ss}</span>
      <span class="method">${e.method}</span>
      <span class="path">${e.path}</span>
      <span class="arrow">→</span>
      <span class="status ${statusCls}">${statusText}</span>
      <span class="ts">${e.elapsedMs}ms</span>
      ${shapeHtml}
    </div>
  `;

  // request body (あれば)
  if (e.body !== undefined) {
    const d = document.createElement("details");
    d.className = "panel";
    d.innerHTML = `<summary>📤 送ったリクエスト本文</summary>`;
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(e.body, null, 2);
    d.appendChild(pre);
    el.appendChild(d);
  }

  // response (あれば、開いた状態で)
  if (e.networkError) {
    const d = document.createElement("details");
    d.className = "panel"; d.open = true;
    d.innerHTML = `<summary>⚠️ ネットワークエラー</summary>`;
    const pre = document.createElement("pre");
    pre.textContent = e.networkError + "\n\n" +
      "→ サーバが起動しているか / API URL が正しいか確認してください";
    d.appendChild(pre);
    el.appendChild(d);
  } else {
    const d = document.createElement("details");
    d.className = "panel";
    d.open = !!(e.shapeErrors && !e.shapeOk);   // shape mismatch のときだけ開く
    d.innerHTML = `<summary>📥 サーバが返した本文 (${e.json == null ? "JSON ではない" : "JSON"})</summary>`;
    const pre = document.createElement("pre");
    pre.textContent = e.json != null
      ? JSON.stringify(e.json, null, 2)
      : (e.rawText || "(空)");
    d.appendChild(pre);
    el.appendChild(d);
  }

  // shape error 詳細
  if (e.shapeErrors && e.shapeErrors.length) {
    const d = document.createElement("details");
    d.className = "panel";
    const lines = e.shapeErrors.map(er =>
      `  ${er.path || "(root)"}: 期待 ${er.want}, 実際 ${er.got}`
    ).join("\n");
    d.innerHTML = `<summary>📐 期待形式との差分</summary>`;
    const pre = document.createElement("pre");
    pre.textContent = lines + "\n\n期待形式:\n" + JSON.stringify(e.expect, null, 2);
    d.appendChild(pre);
    el.appendChild(d);
  }

  return el;
}

// ---- 期待形と違う / エラーが起きたら、画面上部のフィードバック領域に出す ----
function showFeedback(title, result) {
  const fb = $("feedback");
  fb.hidden = false;
  fb.innerHTML = "";
  const h = document.createElement("h3");
  h.textContent = title;
  fb.appendChild(h);

  const reqLine = document.createElement("p");
  reqLine.className = "req-line";
  reqLine.textContent = `${result.method} ${result.path}` +
    (result.body ? "  body: " + JSON.stringify(result.body) : "");
  fb.appendChild(reqLine);

  const sumLine = document.createElement("p");
  sumLine.className = "req-line";
  sumLine.textContent =
    result.networkError ? `ネットワークエラー: ${result.networkError}` :
    `サーバ応答: ${result.status}` +
    (result.json != null ? `, JSON あり` : `, JSON ではない`);
  fb.appendChild(sumLine);

  const det = document.createElement("details"); det.open = true;
  det.innerHTML = "<summary>サーバが返した本文</summary>";
  const pre = document.createElement("pre");
  pre.textContent = result.json != null
    ? JSON.stringify(result.json, null, 2)
    : (result.rawText || result.networkError || "(空)");
  det.appendChild(pre);
  fb.appendChild(det);

  if (result.expect) {
    const expDet = document.createElement("details");
    expDet.innerHTML = "<summary>期待していた形</summary>";
    const expPre = document.createElement("pre");
    expPre.textContent = JSON.stringify(result.expect, null, 2);
    expDet.appendChild(expPre);
    fb.appendChild(expDet);
  }
}
function clearFeedback() { $("feedback").hidden = true; $("feedback").innerHTML = ""; }

// ---- 期待 shape (= API 仕様) -------------------------------------------------
//
// ⚠️ 重要: この SHAPE 定義は docs/api-spec.html の「フロントが期待する shape」
// セクションと内容を一致させる必要があります (= 手動同期)。 サーバ
// (server/app.py) のレスポンス構造を変えるときは、 この 2 箇所と api-spec の
// 「エンドポイント一覧」 のレスポンス例も合わせて更新してください。
const SHAPE = {
  // /api/register, /api/login: user に加えて token (Bearer) が必須
  auth: {
    user: { id: "number", name: "string", display_name: "string", coins: "number" },
    token: "string",
  },
  user: { user: { id: "number", name: "string", display_name: "string", coins: "number" } },
  ok:   { ok: "boolean" },
  gachas: { gachas: [{ id: "number", name: "string", price: "number", pool_size: "number" }] },
  pull: { gacha: "object", character: { id: "number", name: "string", rarity: "number", emoji: "string" }, coins: "number" },
  box:  { user: "object", total_pulls: "number", items: [{ id: "number", name: "string", rarity: "number", emoji: "string", count: "number" }] },
};

// ---- 疎通確認 ---------------------------------------------------------------
$("ping-btn").addEventListener("click", async () => {
  // どんな応答でも OK。 サーバがいるかだけ確認する。
  const r = await call("GET", "/api/me", { expect: SHAPE.user });
  if (r.networkError) {
    showFeedback("⚠️ サーバに繋がりません", r);
  } else {
    // 200 でも 401 でも、ともかくサーバから何かが返れば OK
    setStatus(r.status >= 200 && r.status < 500 ? "ok" : "partial");
  }
});

// ---- 起動時: /api/me を試して、ログイン中ならステージを切替える ----------------
let currentUser = null;
async function bootstrap() {
  const r = await call("GET", "/api/me", { expect: SHAPE.user });
  if (r.shapeOk) { setUser(r.json.user); await loadAfterLogin(); return; }
  showAuth();
}

function setUser(user) {
  currentUser = user;
  $("welcome").hidden = false;
  $("welcome").textContent = `ようこそ ${user.display_name} さん`;
  $("logout-btn").hidden = false;
  $("auth-section").hidden = true;
  $("play-section").hidden = false;
  $("coins").textContent = user.coins;
  clearFeedback();
}
function showAuth() {
  $("auth-section").hidden = false;
  $("play-section").hidden = true;
  $("welcome").hidden = true;
  $("logout-btn").hidden = true;
}

// ---- 認証フォーム -----------------------------------------------------------
$("auth-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  clearFeedback();
  const mode = ev.submitter.dataset.mode;   // "login" or "register"
  const fd = new FormData(ev.target);
  const payload = {
    name: fd.get("name"),
    password: fd.get("password"),
  };
  if (mode === "register") {
    payload.display_name = fd.get("display_name") || fd.get("name");
  }
  const r = await call("POST", `/api/${mode}`, { body: payload, expect: SHAPE.auth });
  if (r.shapeOk) {
    setToken(r.json.token);   // Bearer トークンを保存 (shape チェックで必須なので必ず存在)
    setUser(r.json.user);
    await loadAfterLogin();
  } else {
    showFeedback(
      r.networkError ? "⚠️ サーバに繋がりません" :
      r.status === 401 ? "❌ 認証が通りませんでした" :
      r.status === 400 ? "❌ 入力エラー (サーバが弾きました)" :
      "⚠️ 期待形式の応答が返ってきませんでした",
      r);
  }
});

$("logout-btn").addEventListener("click", async () => {
  await call("POST", "/api/logout", { expect: SHAPE.ok });
  setToken(null);                // Bearer トークンを破棄
  currentUser = null;
  showAuth();
});

// ---- ガチャ一覧/Box ---------------------------------------------------------
async function loadAfterLogin() { await Promise.all([loadGachas(), loadBox()]); }

async function loadGachas() {
  const r = await call("GET", "/api/gacha/list", { expect: SHAPE.gachas });
  const el = $("gacha-list");
  el.innerHTML = "";
  if (!r.shapeOk) {
    showFeedback("⚠️ ガチャ一覧の形式が違います", r);
    return;
  }
  for (const g of r.json.gachas) {
    const card = document.createElement("div");
    card.className = "gacha-card";
    card.innerHTML = `
      <h3>${escapeHtml(g.name)}</h3>
      <div class="meta">価格: ${g.price} coin / 排出 ${g.pool_size} 種</div>
      <div class="row"><button data-id="${g.id}">引く</button></div>
    `;
    card.querySelector("button").addEventListener("click", () => pull(g.id));
    el.appendChild(card);
  }
}

async function pull(gacha_id) {
  clearFeedback();
  const r = await call("POST", "/api/gacha/pull",
                       { body: { gacha_id }, expect: SHAPE.pull });
  if (r.shapeOk) {
    $("coins").textContent = r.json.coins;
    showPullResult(r.json);
    await loadBox();
  } else {
    showFeedback("⚠️ ガチャの応答が期待形式と違います", r);
  }
}

function showPullResult(r) {
  const el = $("pull-result");
  el.hidden = false;
  el.className = `pull-result rarity-${r.character.rarity}`;
  el.innerHTML = `
    <div class="emoji">${escapeHtml(r.character.emoji)}</div>
    <div class="name">${escapeHtml(r.character.name)}</div>
    <div class="stars">${"★".repeat(r.character.rarity)}${"☆".repeat(5 - r.character.rarity)}</div>
    <div class="meta">${escapeHtml(r.gacha.name)} で獲得 (-${r.gacha.price} coin)</div>
  `;
}

$("reload-box-btn").addEventListener("click", loadBox);
async function loadBox() {
  const r = await call("GET", "/api/box", { expect: SHAPE.box });
  if (!r.shapeOk) {
    showFeedback("⚠️ Box の応答が期待形式と違います", r);
    return;
  }
  $("total-pulls").textContent = r.json.total_pulls;
  $("unique-count").textContent = r.json.items.length;
  const el = $("box");
  el.innerHTML = "";
  if (r.json.items.length === 0) {
    el.innerHTML = `<p class="hint">まだ何も持っていません。ガチャを引いてみよう!</p>`;
    return;
  }
  for (const it of r.json.items) {
    const div = document.createElement("div");
    div.className = "char";
    div.dataset.rarity = it.rarity;
    div.innerHTML = `
      <span class="count">×${it.count}</span>
      <div class="emoji">${escapeHtml(it.emoji)}</div>
      <div class="name">${escapeHtml(it.name)}</div>
      <div class="stars">${"★".repeat(it.rarity)}</div>
    `;
    el.appendChild(div);
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// 起動
bootstrap();
