async function api(url, body) {
  const res = await fetch(url, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function fmt(n) {
  return Number(n).toFixed(2);
}

function renderCart(cart) {
  const wrap = document.getElementById("cartWrap");
  const empty = document.getElementById("cartEmpty");
  const itemsEl = document.getElementById("items");

  if (!cart || !cart.items || cart.items.length === 0) {
    wrap.classList.add("hidden");
    empty.classList.remove("hidden");
    return;
  }

  empty.classList.add("hidden");
  wrap.classList.remove("hidden");

  document.getElementById("subtotal").textContent = fmt(cart.subtotal);
  document.getElementById("currency").textContent = cart.currency || "USD";

  itemsEl.innerHTML = "";
  cart.items.forEach((it) => {
    const row = document.createElement("div");
    row.className = "rounded-3xl border border-white/10 bg-white/5 p-5 flex items-center justify-between gap-4";

    row.innerHTML = `
      <div class="min-w-0">
        <div class="font-semibold truncate">${it.title}</div>
        <div class="text-xs text-zinc-500">Item #${it.id}</div>
        <div class="mt-2 text-sm text-zinc-300">${fmt(it.unit_price)} × ${it.qty} = <span class="text-zinc-100 font-semibold">${fmt(it.line_total)}</span></div>
      </div>

      <div class="flex items-center gap-2">
        <button data-dec="${it.id}" class="px-3 py-2 rounded-xl border border-white/15 hover:bg-white/5">-</button>
        <input data-qty="${it.id}" value="${it.qty}" class="w-14 text-center rounded-xl bg-zinc-950 border border-white/10 px-2 py-2" />
        <button data-inc="${it.id}" class="px-3 py-2 rounded-xl border border-white/15 hover:bg-white/5">+</button>
        <button data-rm="${it.id}" class="px-3 py-2 rounded-xl border border-white/15 hover:bg-white/5 text-zinc-300">Remove</button>
      </div>
    `;

    itemsEl.appendChild(row);
  });

  // handlers
  itemsEl.querySelectorAll("[data-inc]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = Number(btn.getAttribute("data-inc"));
      const input = itemsEl.querySelector(`[data-qty="${id}"]`);
      const next = Math.min(99, Number(input.value) + 1);
      const cart = await api("/api/cart/update-qty", { item_id: id, qty: next });
      renderCart(cart);
    });
  });

  itemsEl.querySelectorAll("[data-dec]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = Number(btn.getAttribute("data-dec"));
      const input = itemsEl.querySelector(`[data-qty="${id}"]`);
      const next = Math.max(1, Number(input.value) - 1);
      const cart = await api("/api/cart/update-qty", { item_id: id, qty: next });
      renderCart(cart);
    });
  });

  itemsEl.querySelectorAll("[data-rm]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = Number(btn.getAttribute("data-rm"));
      try {
        const cart = await api("/api/cart/remove", { item_id: id });
        renderCart(cart);
      } catch (e) {
        // cart empty -> api throws 404
        renderCart({ items: [] });
      }
    });
  });

  itemsEl.querySelectorAll("[data-qty]").forEach((input) => {
    input.addEventListener("change", async () => {
      const id = Number(input.getAttribute("data-qty"));
      const next = Math.min(99, Math.max(1, Number(input.value || 1)));
      const cart = await api("/api/cart/update-qty", { item_id: id, qty: next });
      renderCart(cart);
    });
  });
}

async function init() {
  const refreshBtn = document.getElementById("refreshBtn");
  refreshBtn?.addEventListener("click", async () => {
    try {
      const cart = await api("/api/cart");
      renderCart(cart);
    } catch {
      renderCart({ items: [] });
    }
  });

  try {
    const cart = await api("/api/cart");
    renderCart(cart);
  } catch {
    renderCart({ items: [] });
  }
}

init();
