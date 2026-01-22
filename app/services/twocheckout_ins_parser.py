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
    returns: (internal_payment_status, extracted_fields)
    """
    # IPN шлет ключи капсом
    message_type = (pick(payload, "MESSAGE_TYPE", "message_type") or "").upper()

    order_status = pick(payload, "ORDERSTATUS", "order_status", "status")
    invoice_status = pick(payload, "INVOICESTATUS", "invoice_status", "invoiceStatus")
    fraud_status = pick(payload, "FRAUD_STATUS", "fraud_status", "approve_status")

    os_norm = (order_status or "").upper()
    is_norm = (invoice_status or "").upper()
    fr_norm = (fraud_status or "").upper()

    is_fraud = "FRAUD" in message_type or fr_norm in {"DENIED", "REJECTED"}
    is_pending_review = fr_norm in {"UNDER_REVIEW", "PENDING"}
    is_refund = "REFUND" in message_type or os_norm == "REFUND" or is_norm == "REFUNDED"
    is_canceled = os_norm in {"CANCELED", "CANCELLED"}
    paid_words = {
        "PAID", "DEPOSITED", "COMPLETE", "COMPLETED", "PAYMENT_RECEIVED",
        "PAYMENT_AUTHORIZED",
    }
    is_paid = os_norm in paid_words or is_norm in paid_words

    internal = None
    if is_refund:
        internal = "refunded"
    elif is_canceled:
        internal = "canceled"
    elif is_fraud:
        internal = "fraud"
    elif is_pending_review:
        internal = "pending_review"
    elif is_paid:
        internal = "paid"

    extracted = {
        "message_type": message_type or None,
        "order_status": order_status,
        "invoice_status": invoice_status,
        "fraud_status": fraud_status,
    }
    return internal, extracted
