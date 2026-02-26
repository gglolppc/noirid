// /static/js/subscribe.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("subscribe-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const fd = new FormData(form);
    fd.set("source", "footer_form");
    fd.set("page_path", window.location.pathname);

    const params = new URLSearchParams(window.location.search);
    ["utm_source","utm_medium","utm_campaign","utm_content","utm_term"].forEach((k) => {
      const v = params.get(k);
      if (v) fd.set(k, v);
    });

    const res = await fetch("/api/subscribe", { method: "POST", body: fd });
    let data = null;
    try { data = await res.json(); } catch {}

    if (!res.ok || !data?.success) {
      // покажи “что-то пошло не так”
      return;
    }

    // успех
    form.reset();
    const msg = document.getElementById("subscribe-success");
    msg.classList.remove("hidden");
  });
});