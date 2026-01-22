from __future__ import annotations


FINAL = {"paid", "refunded", "canceled"}
# fraud и reversed не финальные, потому что может перейти обратно (OK / retry)


def apply_payment_status(current: str, incoming: str) -> str:
    c = (current or "unpaid").lower()
    n = (incoming or "").lower()

    if not n:
        return c

    # paid -> refunded (норм)
    if c == "paid" and n == "refunded":
        return "refunded"

    # paid -> canceled (обычно нет, но бывает если пришли события не по порядку)
    if c == "paid" and n == "canceled":
        return "paid"  # не даём откатить paid назад

    # refunded — финал
    if c == "refunded":
        return "refunded"

    # canceled — финал (кроме кейса когда уже paid)
    if c == "canceled":
        return "canceled"

    # fraud может позже стать ok/paid
    if n in {"fraud", "fraud_review"}:
        return "fraud"

    # reversed — “платёж отклонён/отозван”, чаще = unpaid с пометкой
    if n == "reversed":
        return "reversed"

    # paid — сильнее всего, кроме refunded
    if n == "paid":
        return "paid"

    # unpaid / pending
    if n in {"unpaid", "pending"}:
        return c

    return c
