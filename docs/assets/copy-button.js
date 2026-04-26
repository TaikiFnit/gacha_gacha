// 各 <pre><code> ブロックの右上に「Copy」ボタンを足す。
// Colab セルに貼り付けるための時短用。
(() => {
  const btnLabel = "Copy";
  const okLabel = "Copied ✓";

  function addButton(pre) {
    if (pre.dataset.copyAttached === "1") return;
    pre.dataset.copyAttached = "1";

    const btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.type = "button";
    btn.textContent = btnLabel;
    pre.appendChild(btn);

    btn.addEventListener("click", async () => {
      const code = pre.querySelector("code");
      const text = (code ? code.innerText : pre.innerText)
        .replace(/Copy ?✓?\s*$/, "");  // ボタン自身のテキストを除外
      try {
        await navigator.clipboard.writeText(text);
      } catch (_e) {
        // フォールバック: 古いブラウザ用
        const ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
      btn.textContent = okLabel;
      btn.classList.add("copied");
      setTimeout(() => {
        btn.textContent = btnLabel;
        btn.classList.remove("copied");
      }, 1500);
    });
  }

  function attachAll() {
    for (const pre of document.querySelectorAll("pre")) addButton(pre);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attachAll);
  } else {
    attachAll();
  }
})();
