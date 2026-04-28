// ch16 / step 2 — フレームワーク非依存の状態 store (~80 行)。
//
// ゴール:
//   subscribe / setState / getState だけの最小ストア。 これで Zustand や
//   Pinia と同じ形のことがフレームワーク無しでできる。
//
// 使い方:
//   import { createStore } from "./step2_state_store.js";
//   const store = createStore({ user: null, coins: 0 });
//   const unsub = store.subscribe(s => console.log(s));
//   store.setState(s => ({ ...s, coins: s.coins + 200 }));

export function createStore(initial) {
  let state = initial;
  const listeners = new Set();

  function getState() { return state; }

  function setState(updater) {
    const next = typeof updater === "function" ? updater(state) : updater;
    if (next === state) return;
    state = next;
    for (const fn of listeners) fn(state);
  }

  function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  }

  return { getState, setState, subscribe };
}

// ---------- 例: ガチャゲーム用ストア ----------
// (このファイル単体で動かすときは下のサンプルを実行できる)
if (typeof window !== "undefined" && window.location?.search?.includes("demo")) {
  const store = createStore({
    user: null,
    coins: 0,
    box: [],
  });
  store.subscribe(s => console.log("[store]", s));
  store.setState(s => ({ ...s, user: { id: 1, name: "alice" }, coins: 1000 }));
  store.setState(s => ({ ...s, coins: s.coins + 200 }));
}
