import httpx
import logging
from app.core.config import settings


log = logging.getLogger("emails")

MAILGUN_API_KEY = settings.MAILGUN_API_KEY
MAILGUN_DOMAIN = "mg.noirid.com"
MAILGUN_FROM = "NOIRID <noreply@mg.noirid.com>"
BASE_URL = "https://noirid.com"  # Твой основной домен


async def send_success_payment_email(email: str, order_number: str):
    if not MAILGUN_API_KEY:
        log.error("MAILGUN_API_KEY is not set in environment variables!")
    url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
    auth = ("api", MAILGUN_API_KEY)

    # Ссылка на твой трэкинг
    tracking_url = f"{BASE_URL}/orders/{order_number}"

    html_content = f"""
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="background-color: #000000; color: #ffffff; font-family: 'Helvetica', Arial, sans-serif; margin: 0; padding: 60px 20px; text-align: center;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h1 style="font-size: 24px; letter-spacing: 8px; text-transform: uppercase; font-weight: 300; margin-bottom: 40px;">
                        NOIRID
                    </h1>

                    <div style="border-top: 1px solid #222; border-bottom: 1px solid #222; padding: 40px 0; margin-bottom: 40px;">
                        <p style="text-transform: uppercase; letter-spacing: 2px; font-size: 12px; color: #888; margin-bottom: 10px;">
                            Status: Confirmed
                        </p>
                        <h2 style="font-size: 20px; font-weight: 300; margin-bottom: 25px;">
                            Payment Received
                        </h2>
                        <p style="font-size: 14px; line-height: 1.6; color: #ccc; margin-bottom: 30px;">
                            Your custom piece is now in production. <br> 
                            We will notify you as soon as it's ready for shipment.
                        </p>

                        <div style="background-color: #111; padding: 15px; display: inline-block; border-radius: 2px;">
                            <span style="font-size: 11px; color: #555; text-transform: uppercase; display: block; margin-bottom: 5px;">Order ID</span>
                            <span style="font-size: 16px; letter-spacing: 3px; font-weight: bold; color: #fff;">{order_number}</span>
                        </div>
                    </div>

                    <div style="margin-top: 20px;">
                        <a href="{tracking_url}" 
                           style="display: inline-block; background-color: #ffffff; color: #000000; padding: 18px 40px; text-decoration: none; font-size: 11px; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; border-radius: 0px;">
                           Track Order
                        </a>
                    </div>

                    <p style="margin-top: 80px; font-size: 10px; letter-spacing: 1px; color: #444; text-transform: uppercase;">
                        Designed for the dark. &copy; 2026 NOIRID.
                    </p>
                </div>
            </body>
        </html>
        """

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                auth=auth,
                data={
                    "from": MAILGUN_FROM,
                    "to": [email],
                    "subject": f"Order {order_number} confirmed | NOIRID",
                    "html": html_content,
                    "text": f"Your order {order_number} is confirmed. Track it here: {tracking_url}",
                },
            )
            response.raise_for_status()
            log.info(f"Email sent to {email} for order {order_number}")
        except Exception as e:
            log.error(f"Mailgun error: {str(e)}")
