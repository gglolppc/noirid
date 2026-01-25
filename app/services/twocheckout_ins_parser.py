from __future__ import annotations


def pick(d: dict, *keys: str) -> str | None:
    for k in keys:
        v = d.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return None


def map_to_internal_status(payload: dict) -> tuple[str | None, dict]:
    """
    Парсит уведомление 2Checkout и возвращает внутренний статус системы.
    Специально адаптировано под физические товары: разделяем холдирование и оплату.
    """
    # 1. Извлекаем данные и сразу в верхний регистр для сравнения
    message_type = (pick(payload, "MESSAGE_TYPE", "message_type") or "").upper()

    # Это те самые переменные, которые упали с ошибкой Unresolved reference
    os_norm = (pick(payload, "ORDERSTATUS", "order_status", "status") or "").upper()
    is_norm = (pick(payload, "INVOICESTATUS", "invoice_status", "invoiceStatus") or "").upper()
    fr_norm = (pick(payload, "FRAUD_STATUS", "fraud_status", "approve_status") or "").upper()

    # 2. Словари статусов
    # Деньги реально получены/списаны (можно отгружать)
    paid_words = {"PAID", "DEPOSITED", "COMPLETE", "COMPLETED", "PAYMENT_RECEIVED", "PURCHASE"}

    # Деньги только заморожены банком (НЕЛЬЗЯ отгружать, ждем списания)
    auth_words = {"PAYMENT_AUTHORIZED", "AUTHONLY", "AUTHORIZED"}

    # Отмены и возвраты
    cancel_words = {"CANCELED", "CANCELLED", "ORDER_CANCELLED"}
    refund_words = {"REFUND", "REFUNDED", "TOTAL_REFUNDED"}

    # 3. Логические флаги
    is_fraud_denied = "FRAUD" in message_type or fr_norm in {"DENIED", "REJECTED"}
    is_pending_review = fr_norm in {"UNDER_REVIEW", "PENDING"}

    is_refund = os_norm in refund_words or is_norm in refund_words or "REFUND" in message_type
    is_canceled = os_norm in cancel_words or is_norm in cancel_words
    is_paid = os_norm in paid_words or is_norm in paid_words
    is_auth = os_norm in auth_words or is_norm in auth_words

    # 4. Выбор внутреннего статуса по приоритету
    internal = None

    if is_fraud_denied:
        internal = "fraud"
    elif is_refund:
        internal = "refunded"
    elif is_canceled:
        internal = "canceled"
    elif is_paid:
        internal = "paid"
    elif is_auth:
        internal = "authorized"
    elif is_pending_review:
        internal = "pending_review"

    extracted = {
        "message_type": message_type or None,
        "order_status": os_norm or None,
        "invoice_status": is_norm or None,
        "fraud_status": fr_norm or None,
    }

    return internal, extracted