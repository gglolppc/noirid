/**
 * NOIRID - Checkout Core Logic (Direct Flow + Loader)
 */

const loader = {
  get el() { return document.getElementById("global-loader"); },
  start: function() {
    if (this.el) {
      this.el.classList.remove("hidden");
      document.body.style.overflow = "hidden"; // Блокируем скролл
    }
  },
  stop: function() {
    if (this.el) {
      this.el.classList.add("hidden");
      document.body.style.overflow = ""; // Возвращаем скролл
    }
  }
};

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

function isFormValid() {
  const form = document.getElementById("checkoutForm");
  if (!form.checkValidity()) {
    form.reportValidity();
    return false;
  }
  return true;
}

function renderPayPalButtons() {
  const container = document.getElementById("paypal-button-container");
  if (!container) return;

  paypal.Buttons({
    style: {
      layout: 'vertical',
      color: 'black',
      shape: 'rect',
      label: 'pay',
      height: 50
    },

    onClick: (data, actions) => {
      clearError();
      if (isFormValid()) {
        return actions.resolve();
      } else {
        return actions.reject();
      }
    },

    createOrder: async () => {
      loader.start(); // ВКЛЮЧАЕМ ЛОАДЕР ПРИ КЛИКЕ
      try {
        const form = document.getElementById("checkoutForm");
        const fd = new FormData(form);

        const country = (
          fd.get("country") ||
          document.getElementById("country-select")?.value ||
          ""
        ).toString().trim().toUpperCase();

        if (!country) throw new Error("Please select a shipping country.");

        const city = (fd.get("city") || "").toString().trim();
        const line1 = (fd.get("line1") || "").toString().trim();
        const postal = (fd.get("postal_code") || "").toString().trim();

        const payload = { country, city, line1, postal_code: postal };

        const orderData = {
          email: (fd.get("email") || "").toString().trim(),
          name: (fd.get("name") || "").toString().trim(),
          phone: ((fd.get("phone") || "").toString().trim() || null),
          shipping_address: { country, city, line1, postal_code: postal || null }
        };

        await postJSON("/api/checkout/create-order", orderData);

        const res = await fetch("/api/payments/paypal/create", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || "PayPal Error");

        loader.stop(); // ВЫКЛЮЧАЕМ, КОГДА ОКНО ПЭЙПАЛА ГОТОВО К ОТКРЫТИЮ
        return data.id;

      } catch (err) {
        loader.stop(); // ВЫКЛЮЧАЕМ ПРИ ОШИБКЕ
        showError(err.message || "Checkout error");
        throw err;
      }
    },

    onApprove: async (data, actions) => {
      loader.start(); // ВКЛЮЧАЕМ ЛОАДЕР СНОВА НА ВРЕМЯ CAPTURE
      try {
        const response = await fetch(`/api/payments/paypal/capture/${data.orderID}`, {
          method: "POST"
        });
        const result = await response.json();

        if (result.status === "success") {
          window.location.href = `/order/${result.order_number}`;
        } else {
          loader.stop();
          showError("Payment confirmation failed.");
        }
      } catch (err) {
        loader.stop();
        showError("System error during payment.");
      }
    },

    onCancel: () => {
      loader.stop(); // ВЫКЛЮЧАЕМ, ЕСЛИ ЗАКРЫЛИ ОКНО ОПЛАТЫ
    },

    onError: (err) => {
      loader.stop(); // ВЫКЛЮЧАЕМ ПРИ ГЛОБАЛЬНОЙ ОШИБКЕ
      console.error("PayPal Global Error:", err);
      showError("PayPal is temporarily unavailable.");
    }
  }).render('#paypal-button-container');
}

function initCountrySelect() {
  const countries = [
    { code: 'RO', name: 'Romania', group: 1 },
    { code: 'DE', name: 'Germany', group: 1 },
    { code: 'GB', name: 'United Kingdom', group: 1 },
    { code: 'MD', name: 'Moldova', group: 2 },
    { code: 'FR', name: 'France', group: 2 },
    { code: 'IT', name: 'Italy', group: 2 },
    { code: 'ES', name: 'Spain', group: 2 },
    { code: 'AT', name: 'Austria', group: 2 },
    { code: 'BE', name: 'Belgium', group: 2 },
    { code: 'NL', name: 'Netherlands', group: 2 },
    { code: 'CH', name: 'Switzerland', group: 2 },
    { code: 'US', name: 'United States', group: 3 },
    { code: 'CA', name: 'Canada', group: 3 },
    { code: 'AU', name: 'Australia', group: 3 },
    { code: 'IL', name: 'Israel', group: 3 },
  ];

  const selectEl = document.getElementById('country-select');
  if (!selectEl) return;

  const sorted = countries.sort((a, b) => {
    if (a.group !== b.group) return a.group - b.group;
    return a.name.localeCompare(b.name);
  });

  sorted.forEach(c => {
    const option = new Option(c.name, c.code);
    selectEl.add(option);
  });

  new Choices(selectEl, {
    searchEnabled: true,
    itemSelectText: '',
    shouldSort: false,
    placeholder: true,
    placeholderValue: 'Select shipping country...',
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initCountrySelect();
  renderPayPalButtons();
});