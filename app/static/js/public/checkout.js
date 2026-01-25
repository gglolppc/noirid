// checkout.js

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Unable to process order");
  return data;
}

function showError(msg) {
  const el = document.getElementById("err");
  if (!el) return;
  el.textContent = "Error: " + msg;
  el.classList.remove("hidden");
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function clearError() {
  const el = document.getElementById("err");
  if (el) el.classList.add("hidden");
}

document.getElementById("checkoutForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError();

  const btn = document.getElementById("payBtn");
  const originalText = btn.textContent;
  
  // State: Loading
  btn.disabled = true;
  btn.textContent = "Processing...";
  btn.classList.add("opacity-50", "scale-[0.98]");

  const fd = new FormData(e.target);

  const payload = {
    email: fd.get("email"),
    name: fd.get("name"),
    phone: fd.get("phone") || null,
    shipping_address: {
      country: fd.get("country"),
      city: fd.get("city"),
      line1: fd.get("line1"),
      line2: fd.get("line2") || null,
      postal_code: fd.get("postal_code") || null,
      notes: fd.get("notes") || null,
    }
  };

  try {
    // 1. Создаем заказ в БД
    await postJSON("/api/checkout/create-order", payload);
    
    // 2. Запрашиваем ссылку на оплату
    const pay = await postJSON("/api/payments/2co/start", {});
    
    if (pay.redirect_url) {
      btn.textContent = "Redirecting to Payment...";
      window.location.assign(pay.redirect_url);
    } else {
      throw new Error("Missing payment link");
    }
  } catch (err) {
    console.error("Checkout failed:", err);
    showError(err.message);
    
    // Reset button
    btn.disabled = false;
    btn.textContent = originalText;
    btn.classList.remove("opacity-50", "scale-[0.98]");
  }
});