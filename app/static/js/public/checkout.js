/**
 * NOIRID - Checkout Core Logic (Direct Flow)
 */

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

/**
 * Валидация формы стандартными средствами браузера
 */
function isFormValid() {
  const form = document.getElementById("checkoutForm");
  if (!form.checkValidity()) {
    form.reportValidity();
    return false;
  }
  return true;
}

/**
 * Инициализация кнопок PayPal
 */
function renderPayPalButtons() {
  const container = document.getElementById("paypal-button-container");
  if (!container) return;

  paypal.Buttons({
    style: {
      layout: 'vertical',
      color: 'black', // Noirid Minimalist
      shape: 'rect',
      label: 'pay',
      height: 50
    },

    // 1. Проверка формы перед открытием окна PayPal
    onClick: (data, actions) => {
      clearError();
      if (isFormValid()) {
        return actions.resolve();
      } else {
        return actions.reject();
      }
    },

    // 2. Создание заказа в нашей БД + создание заказа в PayPal
    createOrder: async () => {
      try {
        const form = document.getElementById("checkoutForm");
        const fd = new FormData(form);

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

        // Сохраняем данные клиента и создаем запись в БД
        await postJSON("/api/checkout/create-order", payload);

        // Запрашиваем создание заказа у PayPal (наш бэк создаст и Payment в базе)
        const res = await fetch("/api/payments/paypal/create", { method: "POST" });
        const paypalOrder = await res.json();

        if (!paypalOrder.id) throw new Error("PayPal initiation failed");

        return paypalOrder.id;
      } catch (err) {
        showError(err.message);
        throw err; // Останавливает процесс PayPal
      }
    },

    // 3. Подтверждение оплаты (Capture)
    onApprove: async (data, actions) => {
      try {
        const res = await fetch(`/api/payments/paypal/capture/${data.orderID}`, {
          method: "POST"
        });
        const result = await res.json();

        if (result.status === "success") {
          // Редирект на страницу заказа по его номеру NRD-...
          window.location.href = `/order/${result.order_number}`;
        } else {
          showError("Payment failed. Please check your balance or try another method.");
        }
      } catch (err) {
        console.error("Capture error:", err);
        showError("System error during payment confirmation.");
      }
    },

    onError: (err) => {
      console.error("PayPal Error:", err);
      showError("PayPal is currently unavailable. Please refresh or try later.");
    }
  }).render('#paypal-button-container');
}

/**
 * Настройка селекта стран с поиском (Choices.js)
 */
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
    placeholderValue: 'Select country',
  });
}

// Запуск при загрузке
document.addEventListener('DOMContentLoaded', () => {
  initCountrySelect();
  renderPayPalButtons();
});