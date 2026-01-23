async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

function showError(msg) {
  const el = document.getElementById("err");
  el.textContent = msg;
  el.classList.remove("hidden");
}

document.getElementById("checkoutForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const btn = document.getElementById("payBtn");
  btn.disabled = true;
  btn.classList.add("opacity-60");

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
    await postJSON("/api/checkout/create-order", payload);
    const pay = await postJSON("/api/payments/2co/start", {});
    window.location.assign(pay.redirect_url);
    return;
  } catch (err) {
    showError(err.message || "Failed");
  } finally {
    btn.disabled = false;
    btn.classList.remove("opacity-60");
  }
});
