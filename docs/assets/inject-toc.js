// 各章ページの <aside class="sidebar"> に目次を流し込む簡易スクリプト。
// fetch が file:// でブロックされるブラウザもあるため、
// `python -m http.server 5501 --directory docs` 経由での閲覧を推奨。
(async () => {
  const sidebar = document.querySelector("aside.sidebar");
  if (!sidebar) return;
  try {
    const html = await fetch("./assets/toc.html").then(r => r.text());
    sidebar.innerHTML = html;
  } catch (_e) {
    sidebar.innerHTML = '<p style="padding:12px;color:#6b7280;font-size:13px;">' +
      '目次の読み込みに失敗。<br>' +
      '<code>python -m http.server</code> 経由で開いてください。</p>';
    return;
  }
  const here = location.pathname.split("/").pop() || "index.html";
  for (const a of sidebar.querySelectorAll("a[data-href]")) {
    a.href = a.dataset.href;
    if (a.dataset.href === here) a.classList.add("active");
  }
})();
