// cart.js

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
  document.getElementById("total").textContent = fmt(cart.total || 0);
  
  const currencyStr = cart.currency || "USD";
  document.querySelectorAll(".currency").forEach((el) => {
    el.textContent = currencyStr;
  });

  itemsEl.innerHTML = "";
  cart.items.forEach((it) => {
    const row = document.createElement("div");
    const personalizationEntries = Object.entries(it.personalization || {})
      .filter(([, value]) => value !== null && value !== undefined && String(value).trim() !== "")
      .map(([key, value]) => `${key}: ${value}`);
    const personalizationLine = personalizationEntries.length
      ? `<div class="text-xs text-zinc-400 font-light flex items-center gap-2 justify-center md:justify-start">
           <span class="w-1 h-1 rounded-full bg-white/30"></span>
           Personalization: <span class="text-white/80 italic">${personalizationEntries.join(", ")}</span>
         </div>`
      : "";
    // Карточка товара: белый текст, серый вторичный текст
    row.className = "group relative flex flex-col md:flex-row items-center gap-8 py-8 border-b border-white/5 last:border-0";

    row.innerHTML = `
      <div class="shrink-0 w-24 h-32 rounded-2xl bg-white/[0.03] border border-white/10 flex items-center justify-center overflow-hidden">
          ${
            it.preview_url
              ? `<img src="${it.preview_url}" alt="${it.title}" class="w-full h-full object-cover" />`
              : `<span class="text-[9px] uppercase tracking-widest text-zinc-600 italic">Noirid</span>`
          }
      </div>

      <div class="flex-1 min-w-0 text-center md:text-left">
        <div class="text-xl font-medium text-white mb-1">${it.title}</div>
        <div class="text-[10px] uppercase tracking-widest text-zinc-500 mb-3 italic">Ref. #00${it.id}</div>
        
        ${personalizationLine}
      </div>

      <div class="flex flex-col items-center md:items-end gap-4">
        <div class="flex items-center gap-4 bg-white/[0.03] border border-white/10 p-1 rounded-full">
          <button data-dec="${it.id}" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/10 text-white transition transition-colors">-</button>
          <span class="text-xs font-medium text-white w-4 text-center">${it.qty}</span>
          <button data-inc="${it.id}" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/10 text-white transition transition-colors">+</button>
        </div>
        
        <div class="text-right">
          <div class="text-white font-medium">${fmt(it.line_total)} <span class="text-[10px] text-zinc-500 uppercase">${currencyStr}</span></div>
          <button data-rm="${it.id}" class="mt-1 text-[10px] uppercase tracking-widest text-zinc-600 hover:text-white transition-colors underline underline-offset-4">
            Remove
          </button>
        </div>
      </div>
    `;

    itemsEl.appendChild(row);
  });

  // Привязка событий (остается той же, так как ID те же)
  attachEvents(itemsEl);
}

function attachEvents(container) {
  container.querySelectorAll("[data-inc]").forEach((btn) => {
    btn.onclick = async () => {
      const id = Number(btn.getAttribute("data-inc"));
      const currentQty = parseInt(btn.previousElementSibling.textContent);
      const cart = await api("/api/cart/update-qty", { item_id: id, qty: currentQty + 1 });
      renderCart(cart);
    };
  });

  container.querySelectorAll("[data-dec]").forEach((btn) => {
    btn.onclick = async () => {
      const id = Number(btn.getAttribute("data-dec"));
      const currentQty = parseInt(btn.nextElementSibling.textContent);
      if (currentQty > 1) {
        const cart = await api("/api/cart/update-qty", { item_id: id, qty: currentQty - 1 });
        renderCart(cart);
      }
    };
  });

  container.querySelectorAll("[data-rm]").forEach((btn) => {
    btn.onclick = async () => {
      const id = Number(btn.getAttribute("data-rm"));
      try {
        const cart = await api("/api/cart/remove", { item_id: id });
        renderCart(cart);
      } catch (e) {
        renderCart({ items: [] });
      }
    };
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
