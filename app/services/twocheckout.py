from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import md5
from urllib.parse import urlencode

import hmac

import hashlib


@dataclass(frozen=True)
class TwoCOConfig:
    merchant_code: str   # sid
    secret_word: str
    secret_key: str
    demo: bool
    return_url: str      # x_receipt_link_url


class TwoCOService:
    CHECKOUT_URL = "https://www.2checkout.com/checkout/purchase"

    @staticmethod
    def build_hosted_checkout_url(cfg: TwoCOConfig, *, order_id: str, total: Decimal, currency: str, title: str) -> str:
        # Hosted checkout params :contentReference[oaicite:2]{index=2}
        params = {
            "sid": cfg.merchant_code,
            "mode": "2CO",
            "currency_code": currency,
            "merchant_order_id": order_id,
            "x_receipt_link_url": cfg.return_url,
            # один line item (можешь разнести на несколько, но нахер пока)
            "li_0_type": "product",
            "li_0_name": title[:128],
            "li_0_quantity": 1,
            "li_0_price": f"{total:.2f}",
            "li_0_tangible": "Y",
        }
        if cfg.demo:
            params["demo"] = "Y"

        return f"{TwoCOService.CHECKOUT_URL}?{urlencode(params)}"

    @staticmethod
    def verify_return_md5(
        *,
        secret_word: str,
        sid: str,
        order_number: str,
        total: str,
        received_key: str,
        is_demo: bool,
    ) -> bool:
        # Return Process: UPPERCASE(MD5(secretWord + sid + order_number + total)) :contentReference[oaicite:3]{index=3}
        # Demo: order_number в хэше = "1" :contentReference[oaicite:4]{index=4}
        order_for_hash = "1" if is_demo else str(order_number)
        s = f"{secret_word}{sid}{order_for_hash}{total}"
        calc = md5(s.encode("utf-8")).hexdigest().upper()
        return calc == (received_key or "").upper()


    @staticmethod
    def verify_ins_hash_invoice(cfg: TwoCOConfig, payload: dict) -> bool:
        # INS invoice hash: HMAC(algo, secretKey, sale_id + merchant_code + invoice_id + secret_word) :contentReference[oaicite:5]{index=5}
        raw = payload.get("hash", "")
        if ":" not in raw:
            return False
        algo_raw, received = raw.split(":", 1)

        # python hmac expects e.g. "sha256" or "sha3_256"
        algo = algo_raw.replace("-", "_").lower()

        sale_id = str(payload.get("sale_id", ""))
        invoice_id = str(payload.get("invoice_id", ""))

        msg = f"{sale_id}{cfg.merchant_code}{invoice_id}{cfg.secret_word}".encode("utf-8")
        calc = hmac.new(cfg.secret_key.encode("utf-8"), msg, algo).hexdigest().upper()

        return calc == received.upper()

    @staticmethod
    def verify_ipn_signature_sha2_256(secret_key: str, items: list[tuple[str, object]]) -> bool:
        received = None
        src = ""

        for key, value in items:
            if key == "SIGNATURE_SHA2_256":
                received = str(value or "")
                continue

            # как и раньше: длина в байтах + значение
            val_str = "" if value is None else str(value)
            src += f"{len(val_str.encode('utf-8'))}{val_str}"

        if not received:
            return False

        calc = hmac.new(
            secret_key.encode("utf-8"),
            src.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return calc.lower() == received.lower()

    @staticmethod
    def calculate_ipn_response(secret_key: str, payload: dict) -> str:
        """
        Формирование обязательного ответа для 2Checkout.
        Без этого ответа 2CO будет слать уведомление повторно.
        """
        ipn_pid = payload.get("IPN_PID", "")
        ipn_pname = payload.get("IPN_PNAME", "")
        ipn_date = payload.get("IPN_DATE", "")

        # Формула подтверждения: <EPAYMENT>DATE|HASH</EPAYMENT>
        # Где HASH — это HMAC-SHA256 от IPN_DATE
        res_hash = hmac.new(
            secret_key.encode("utf-8"),
            ipn_date.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return f"<EPAYMENT>{ipn_date}|{res_hash}</EPAYMENT>"