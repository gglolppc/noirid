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
    Специально адаптировано под физические товары.
    """
    # 1. Извлекаем сырые данные (IPN шлет ключи капсом, INS может слать в camelCase)
    message_type = (pick(payload, "MESSAGE_TYPE", "message_type") or "").upper()
    order_status = (pick(payload, "ORDERSTATUS", "order_status", "status") or "").upper()
    invoice_status = (pick(payload, "INVOICESTATUS", "invoice_status", "invoiceStatus") or "").upper()
    fraud_status = (pick(payload, "FRAUD_STATUS", "fraud_status", "approve_status") or "").upper()

    # 2. Определяем группы статусов
    # Деньги реально списаны и подтверждены
    paid_words = {"PAID", "DEPOSITED", "COMPLETE", "COMPLETED", "PAYMENT_RECEIVED", "PURCHASE"}

    # Деньги только заморожены (Hold), 2CO еще может их вернуть без твоего участия
    auth_words = {"PAYMENT_AUTHORIZED", "AUTHONLY", "AUTHORIZED"}

    # Статусы отмены
    cancel_words = {"CANCELED", "CANCELLED", "ORDER_CANCELLED"}

    # Статусы возврата
    refund_words = {"REFUND", "REFUNDED", "TOTAL_REFUNDED"}

    # 3. Флаги состояний
    is_fraud_denied = "FRAUD" in message_type or fraud_status in {"DENIED", "REJECTED"}
    is_pending_review = fraud_status in {"UNDER_REVIEW", "PENDING"}

    is_refund = os_norm in refund_words or is_norm in refund_words or "REFUND" in message_type
    is_canceled = os_norm in cancel_words or is_norm in cancel_words
    is_paid = os_norm in paid_words or is_norm in paid_words
    is_auth = os_norm in auth_words or is_norm in auth_words

    # 4. Приоритизация выбора внутреннего статуса (сверху вниз по важности)
    internal = None

    if is_fraud_denied:
        internal = "fraud"  # Сразу стоп, риск!
    elif is_refund:
        internal = "refunded"  # Деньги вернули
    elif is_canceled:
        internal = "canceled"  # Заказ отменен
    elif is_paid:
        internal = "paid"  # Можно отправлять товар
    elif is_auth:
        internal = "authorized"  # Деньги на холде. Ждем COMPLETE.
    elif is_pending_review:
        internal = "pending_review"  # 2CO проверяет транзакцию вручную

    extracted = {
        "message_type": message_type or None,
        "order_status": order_status or None,
        "invoice_status": invoice_status or None,
        "fraud_status": fraud_status or None,
    }

    return internal, extracted