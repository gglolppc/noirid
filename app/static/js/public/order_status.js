async function getJSON(url) {
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function setText(id, txt) {
  const el = document.getElementById(id);
  if (el) el.textContent = txt;
}

function updateUI(s) {
  setText("payStatus", s.payment_status);
  setText("orderStatus", s.status);

  const hint = document.getElementById("hint");
  const retry = document.getElementById("retryPayBtn");

  const pay = (s.payment_status || "").toLowerCase();
  const st = (s.status || "").toLowerCase();

  if (pay === "paid") {
    fetch("/api/cart/clear", { method: "POST" }).catch(()=>{});
    hint.innerHTML = "✅ Payment confirmed. You're done.";
    retry.classList.add("hidden");
    return;
  }

  if (pay === "fraud") {
    hint.innerHTML = "⚠️ Payment flagged for review (fraud). Don’t ship yet.";
    retry.classList.remove("hidden");
    return;
  }

  if (pay === "canceled" || pay === "reversed") {
    hint.innerHTML = "❌ Payment canceled/declined. You can try again.";
    retry.classList.remove("hidden");
    return;
  }

  hint.innerHTML = "⏳ Waiting for confirmation (webhook). This can take some seconds.";
  retry.classList.add("hidden");
}

async function refresh() {
  const s = await getJSON(`/api/orders/${ORDER_ID}/status`);
  updateUI(s);
  return s;
}

document.getElementById("refreshBtn")?.addEventListener("click", () => {
  refresh().catch(console.error);
});

// polling каждые 3 сек, максимум 2 минуты
(async function poll() {
  try {
    const s = await refresh();
    if ((s.payment_status || "").toLowerCase() === "paid") return;
    if (["canceled", "refunded"].includes((s.payment_status || "").toLowerCase())) return;
  } catch (e) {}

  let ticks = 0;
  const t = setInterval(async () => {
    ticks += 1;
    try {
      const s = await refresh();
      const ps = (s.payment_status || "").toLowerCase();
      if (ps === "paid" || ps === "refunded" || ps === "canceled") {
        clearInterval(t);
      }
    } catch {}
    if (ticks >= 40) clearInterval(t); // ~120 сек
  }, 3000);
})();
