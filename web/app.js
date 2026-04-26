// gacha_gacha フロントエンド (フレームワーク無し / モジュール 1 つ)
// ----------------------------------------------------------------
// 教材的な狙い: fetch で JSON を投げる、Cookie が credentials で送られる、
// 受け取った JSON を DOM に貼る、というブラウザ側の最小ループだけを書く。

const API_BASE = "http://localhost:8000";
document.getElementById("api-base").textContent = API_BASE;

// --- API 呼び出しの薄いラッパ ----------------------------------
async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(API_BASE + path, {
    method,
    credentials: "include",   // ← Cookie をクロスオリジンでも送る
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch (_) { /* 空ボディもOK */ }
  if (!res.ok) {
    const err = new Error(data?.error || `HTTP ${res.status}`);
    err.status = res.status;
    err.payload = data;
    throw err;
  }
  return data;
}

// --- 状態 ------------------------------------------------------
let currentUser = null;

// --- 起動時 ----------------------------------------------------
async function bootstrap() {
  try {
    const { user } = await api("/api/me");
    setUser(user);
    await loadAfterLogin();
  } catch (e) {
    if (e.status === 401) {
      // 未ログイン状態。ログイン画面を出すだけ。
      showAuth();
    } else {
      showError(`接続失敗: ${e.message}`);
    }
  }
}

function setUser(user) {
  currentUser = user;
  document.getElementById("welcome").hidden = false;
  document.getElementById("welcome").textContent =
    `ようこそ ${user.display_name} さん`;
  document.getElementById("logout-btn").hidden = false;
  document.getElementById("auth-section").hidden = true;
  document.getElementById("play-section").hidden = false;
  document.getElementById("coins").textContent = user.coins;
}

function showAuth() {
  document.getElementById("auth-section").hidden = false;
  document.getElementById("play-section").hidden = true;
  document.getElementById("welcome").hidden = true;
  document.getElementById("logout-btn").hidden = true;
}

function showError(msg) {
  const el = document.getElementById("auth-error");
  el.textContent = msg;
  el.hidden = false;
}
function hideError() {
  document.getElementById("auth-error").hidden = true;
}

// --- 認証フォーム ---------------------------------------------
document.getElementById("auth-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  hideError();
  const mode = ev.submitter.dataset.mode;   // 'login' or 'register'
  const fd = new FormData(ev.target);
  const payload = {
    name: fd.get("name"),
    password: fd.get("password"),
  };
  if (mode === "register") {
    payload.display_name = fd.get("display_name") || fd.get("name");
  }
  try {
    const { user } = await api(`/api/${mode}`, { method: "POST", body: payload });
    setUser(user);
    await loadAfterLogin();
  } catch (e) {
    showError(e.message);
  }
});

document.getElementById("logout-btn").addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  currentUser = null;
  showAuth();
});

// --- ログイン後ロード ----------------------------------------
async function loadAfterLogin() {
  await Promise.all([loadGachas(), loadBox()]);
}

async function loadGachas() {
  const { gachas } = await api("/api/gacha/list");
  const el = document.getElementById("gacha-list");
  el.innerHTML = "";
  for (const g of gachas) {
    const card = document.createElement("div");
    card.className = "gacha-card";
    card.innerHTML = `
      <h3>${g.name}</h3>
      <div class="meta">価格: ${g.price} coin / 排出 ${g.pool_size} 種</div>
      <div class="row">
        <button data-id="${g.id}">引く</button>
      </div>
    `;
    card.querySelector("button").addEventListener("click", () => pull(g.id));
    el.appendChild(card);
  }
}

async function pull(gacha_id) {
  try {
    const r = await api("/api/gacha/pull", {
      method: "POST", body: { gacha_id },
    });
    document.getElementById("coins").textContent = r.coins;
    showPullResult(r);
    await loadBox();
  } catch (e) {
    showError(e.message);
  }
}

function showPullResult(r) {
  const el = document.getElementById("pull-result");
  el.hidden = false;
  el.className = `pull-result rarity-${r.character.rarity}`;
  el.innerHTML = `
    <div class="emoji">${r.character.emoji}</div>
    <div class="name">${r.character.name}</div>
    <div class="stars">${"★".repeat(r.character.rarity)}${"☆".repeat(5 - r.character.rarity)}</div>
    <div class="meta">${r.gacha.name} で獲得 (-${r.gacha.price} coin)</div>
  `;
}

// --- Box -----------------------------------------------------
document.getElementById("reload-box-btn").addEventListener("click", loadBox);

async function loadBox() {
  const { items, total_pulls } = await api("/api/box");
  document.getElementById("total-pulls").textContent = total_pulls;
  document.getElementById("unique-count").textContent = items.length;
  const el = document.getElementById("box");
  el.innerHTML = "";
  if (items.length === 0) {
    el.innerHTML = `<p class="hint">まだ何も持っていません。ガチャを引いてみよう！</p>`;
    return;
  }
  for (const it of items) {
    const div = document.createElement("div");
    div.className = "char";
    div.dataset.rarity = it.rarity;
    div.innerHTML = `
      <span class="count">×${it.count}</span>
      <div class="emoji">${it.emoji}</div>
      <div class="name">${it.name}</div>
      <div class="stars">${"★".repeat(it.rarity)}</div>
    `;
    el.appendChild(div);
  }
}

bootstrap();
