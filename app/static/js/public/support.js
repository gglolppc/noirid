document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("supportForm");
  const overlay = document.getElementById("supportOverlay");
  const closeBtn = document.getElementById("supportOverlayClose");

  if (!form || !overlay) return;

  let autoCloseTimer = null;

  function openOverlay() {
    overlay.classList.remove("hidden");
    overlay.classList.add("flex");

    document.documentElement.classList.add("overflow-hidden");
    document.body.classList.add("overflow-hidden");

    overlay.animate(
      [{ opacity: 0 }, { opacity: 1 }],
      { duration: 180, easing: "ease-out" }
    );

    clearTimeout(autoCloseTimer);
    autoCloseTimer = setTimeout(closeOverlay, 5000);
  }

  function closeOverlay() {
    clearTimeout(autoCloseTimer);

    const anim = overlay.animate(
      [{ opacity: 1 }, { opacity: 0 }],
      { duration: 160, easing: "ease-in" }
    );

    anim.onfinish = () => {
      overlay.classList.add("hidden");
      overlay.classList.remove("flex");

      document.documentElement.classList.remove("overflow-hidden");
      document.body.classList.remove("overflow-hidden");
    };
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", closeOverlay);
  }

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeOverlay();
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !overlay.classList.contains("hidden")) {
      closeOverlay();
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);

    try {
      const res = await fetch(form.action, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "fetch"
        }
      });

      if (!res.ok) throw new Error("Request failed");

      const data = await res.json();

      if (data?.success) {
        form.reset();
        openOverlay();
      } else {
        throw new Error("Bad response");
      }

    } catch (err) {
      console.error(err);
      alert("Something went wrong. Please try again.");
    }
  });
});