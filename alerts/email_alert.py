# alerts/email_alert.py

import smtplib
from email.mime.text import MIMEText

from config import (
    EMAIL_ENABLED,
    GMAIL_USERNAME,
    GMAIL_APP_PASSWORD,
    RECEIVER_EMAIL,
)


def send_price_alert(product: dict, target_price: float):
    if not EMAIL_ENABLED:
        print("📧 Email disabled (EMAIL_ENABLED is false). Skipping alert.")
        return

    if not all([GMAIL_USERNAME, GMAIL_APP_PASSWORD, RECEIVER_EMAIL]):
        print("📧 Email config missing. Skipping alert.")
        return

    body = f"""
    <h3>Price Alert Triggered</h3>
    <p><strong>Product:</strong> {product.get("title")}</p>
    <p><strong>ASIN:</strong> {product.get("asin")}</p>
    <p><strong>Current Price:</strong> {product.get("price")}</p>
    <p><strong>Target Price:</strong> {target_price}</p>
    <p><a href="{product.get("url")}">View on Amazon</a></p>
    """

    msg = MIMEText(body, "html")
    msg["Subject"] = f"Price Alert: {product.get('title')}"
    msg["From"] = GMAIL_USERNAME
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USERNAME, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Price alert email sent to {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
