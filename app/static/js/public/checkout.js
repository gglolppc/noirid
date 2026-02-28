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
  // 🇪🇺 Core EU (Group 1 — основные рынки)
  { code: 'RO', name: 'Romania', group: 1 },
  { code: 'DE', name: 'Germany', group: 1 },
  { code: 'FR', name: 'France', group: 1 },
  { code: 'IT', name: 'Italy', group: 1 },
  { code: 'ES', name: 'Spain', group: 1 },
  { code: 'NL', name: 'Netherlands', group: 1 },
  { code: 'BE', name: 'Belgium', group: 1 },
  { code: 'AT', name: 'Austria', group: 1 },
  { code: 'IE', name: 'Ireland', group: 1 },
  { code: 'PT', name: 'Portugal', group: 1 },
  { code: 'SE', name: 'Sweden', group: 1 },
  { code: 'DK', name: 'Denmark', group: 1 },
  { code: 'FI', name: 'Finland', group: 1 },
  { code: 'PL', name: 'Poland', group: 1 },
  { code: 'CZ', name: 'Czech Republic', group: 1 },
  { code: 'HU', name: 'Hungary', group: 1 },

  { code: 'GR', name: 'Greece', group: 1 },
  { code: 'HR', name: 'Croatia', group: 1 },
  { code: 'SK', name: 'Slovakia', group: 1 },
  { code: 'SI', name: 'Slovenia', group: 1 },
  { code: 'BG', name: 'Bulgaria', group: 1 },
  { code: 'EE', name: 'Estonia', group: 1 },
  { code: 'LV', name: 'Latvia', group: 1 },
  { code: 'LT', name: 'Lithuania', group: 1 },
  { code: 'LU', name: 'Luxembourg', group: 1 },

  // 🇪🇺 Non-EU but Europe (Group 2)
  { code: 'GB', name: 'United Kingdom', group: 2 },
  { code: 'CH', name: 'Switzerland', group: 2 },
  { code: 'NO', name: 'Norway', group: 2 },
  { code: 'IS', name: 'Iceland', group: 2 },
  { code: 'LI', name: 'Liechtenstein', group: 2 },
  { code: 'RS', name: 'Serbia', group: 2 },
  { code: 'UA', name: 'Ukraine', group: 2 },
  { code: 'MD', name: 'Moldova', group: 2 },
  { code: 'AL', name: 'Albania', group: 2 },
  { code: 'MK', name: 'North Macedonia', group: 2 },
  { code: 'ME', name: 'Montenegro', group: 2 },
  { code: 'BA', name: 'Bosnia and Herzegovina', group: 2 },

  // 🌍 Other (Group 3 — вне Европы, но адекватные рынки)
  { code: 'CA', name: 'Canada', group: 3 },
  { code: 'AU', name: 'Australia', group: 3 },
];

  const selectEl = document.getElementById('country-select');
  const autofillSelect = document.getElementById('country-autofill-select');
  if (!selectEl) return;

  const sorted = countries.sort((a, b) => {
    if (a.group !== b.group) return a.group - b.group;
    return a.name.localeCompare(b.name);
  });

  // === Заполняем ОБА селекта ===
  sorted.forEach(c => {
    const option = new Option(c.name, c.code);
    selectEl.add(option);

    if (autofillSelect) {
      autofillSelect.add(new Option(c.name, c.code));
    }
  });

  const codeSet = new Set(countries.map(c => c.code));

  // Инициализируем Choices только основной селект
  const choices = new Choices(selectEl, {
    searchEnabled: true,
    itemSelectText: '',
    shouldSort: false,
    placeholder: true,
    placeholderValue: 'Select shipping country...',
  });

  // === НОВАЯ функция синхронизации (гораздо проще) ===
  const applyAutofill = () => {
    if (!autofillSelect) return;
    const code = (autofillSelect.value || '').toString().trim().toUpperCase();

    if (code && codeSet.has(code)) {
      selectEl.value = code;
      choices.setChoiceByValue(code);
    }
  };

  // Слушаем события + поллинг (браузер иногда заполняет очень поздно)
  if (autofillSelect) {
    autofillSelect.addEventListener('change', applyAutofill);
    autofillSelect.addEventListener('input', applyAutofill);

    // Поллинг — ловим autofill, который срабатывает до/после загрузки
    setTimeout(applyAutofill, 100);
    setTimeout(applyAutofill, 300);
    setTimeout(applyAutofill, 800);
    setTimeout(applyAutofill, 1500);

    // Дополнительно при возврате на вкладку и фокусе
    window.addEventListener('focus', () => setTimeout(applyAutofill, 50));
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) setTimeout(applyAutofill, 50);
    });
  }

  // Хак для очень позднего autofill (некоторые версии Chrome/Firefox)
  const observer = new MutationObserver(applyAutofill);
  if (autofillSelect) observer.observe(autofillSelect, { attributes: true, attributeFilter: ['value'] });
}

document.addEventListener('DOMContentLoaded', () => {
  initCountrySelect();
  renderPayPalButtons();
});