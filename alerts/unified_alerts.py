# alerts/unified_alerts.py

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
import config


class AlertManager:
    """Unified alert system for all notification channels"""

    @staticmethod
    def send_email(data: Dict, target_price: float = None, stock_alert: bool = False):
        """Send email alert"""
        if not config.EMAIL_ENABLED:
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = config.GMAIL_USERNAME
            msg["To"] = config.RECEIVER_EMAIL

            if stock_alert:
                msg["Subject"] = f"Stock Alert: {data['title'][:50]}"
                body = f"""
Stock Alert!

Product: {data['title']}
ASIN: {data['asin']}
Stock Status: {data['stock']}
Current Price: {data['price_raw']}

View on Amazon: {data['url']}
"""
            else:
                msg["Subject"] = f"Price Drop Alert: {data['title'][:50]}"
                body = f"""
Price Drop Alert!

Product: {data['title']}
ASIN: {data['asin']}
Current Price: ${data['price']:.2f}
Target Price: ${target_price:.2f}
You Save: ${target_price - data['price']:.2f}

Stock Status: {data['stock']}
Rating: {data['rating_raw']}
Reviews: {data['reviews_raw']}

View on Amazon: {data['url']}
"""

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(config.GMAIL_USERNAME, config.GMAIL_APP_PASSWORD)
                server.send_message(msg)

            print("[OK] Email alert sent")
        except Exception as e:
            print(f"[!] Email alert failed: {e}")

    @staticmethod
    def send_sms(data: Dict, target_price: float = None, stock_alert: bool = False):
        """Send SMS via Twilio"""
        if not config.SMS_ENABLED:
            return

        try:
            from twilio.rest import Client

            client = Client(config.TWILIO_ACCOUNT_SID,
                            config.TWILIO_AUTH_TOKEN)

            if stock_alert:
                message_body = f"Stock Alert: {data['title'][:40]} is now {data['stock']}!"
            else:
                message_body = f"Price Drop: {data['title'][:40]} is now ${data['price']:.2f} (target: ${target_price:.2f})"

            message = client.messages.create(
                body=message_body,
                from_=config.TWILIO_PHONE_NUMBER,
                to=config.RECEIVER_PHONE_NUMBER
            )

            print(f"[OK] SMS alert sent (SID: {message.sid})")
        except Exception as e:
            print(f"[!] SMS alert failed: {e}")

    @staticmethod
    def send_telegram(data: Dict, target_price: float = None, stock_alert: bool = False):
        """Send Telegram message"""
        if not config.TELEGRAM_ENABLED:
            return

        try:
            if stock_alert:
                text = f"""
Stock Alert

Product: {data['title'][:100]}
ASIN: {data['asin']}
Stock: {data['stock']}
Price: {data['price_raw']}

View on Amazon: {data['url']}
"""
            else:
                text = f"""
Price Drop Alert!

Product: {data['title'][:100]}
ASIN: {data['asin']}
Current: ${data['price']:.2f}
Target: ${target_price:.2f}
You Save: ${target_price - data['price']:.2f}
Stock: {data['stock']}
Rating: {data['rating_raw']}

View on Amazon: {data['url']}
"""

            url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": text,
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            print("[OK] Telegram alert sent")
        except Exception as e:
            print(f"[!] Telegram alert failed: {e}")

    @staticmethod
    def send_discord(data: Dict, target_price: float = None, stock_alert: bool = False):
        """Send Discord webhook message"""
        if not config.DISCORD_ENABLED:
            return

        try:
            if stock_alert:
                embed = {
                    "title": "Stock Alert",
                    "description": data['title'][:200],
                    "color": 3447003,
                    "fields": [
                        {"name": "ASIN",
                            "value": data['asin'], "inline": True},
                        {"name": "Stock Status",
                            "value": data['stock'], "inline": True},
                        {"name": "Price",
                            "value": data['price_raw'], "inline": True},
                    ],
                    "url": data['url']
                }
            else:
                embed = {
                    "title": "Price Drop Alert!",
                    "description": data['title'][:200],
                    "color": 65280,
                    "fields": [
                        {"name": "ASIN",
                            "value": data['asin'], "inline": True},
                        {"name": "Current Price",
                            "value": f"${data['price']:.2f}", "inline": True},
                        {"name": "Target Price",
                            "value": f"${target_price:.2f}", "inline": True},
                        {"name": "You Save",
                            "value": f"${target_price - data['price']:.2f}", "inline": True},
                        {"name": "Stock",
                            "value": data['stock'], "inline": True},
                        {"name": "Rating",
                            "value": data['rating_raw'] or "N/A", "inline": True},
                    ],
                    "url": data['url']
                }

            payload = {"embeds": [embed]}

            response = requests.post(
                config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            response.raise_for_status()

            print("[OK] Discord alert sent")
        except Exception as e:
            print(f"[!] Discord alert failed: {e}")

    @staticmethod
    def send_slack(data: Dict, target_price: float = None, stock_alert: bool = False):
        """Send Slack webhook message"""
        if not config.SLACK_ENABLED:
            return

        try:
            if stock_alert:
                text = f"*Stock Alert*\n{data['title'][:100]}\nStock: *{data['stock']}*"
                color = "#0000FF"
            else:
                text = f"*Price Drop Alert!*\n{data['title'][:100]}\nCurrent: ${data['price']:.2f} | Target: ${target_price:.2f}"
                color = "#00FF00"

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "text": text,
                        "fields": [
                            {"title": "ASIN",
                                "value": data['asin'], "short": True},
                            {"title": "Price",
                                "value": data['price_raw'], "short": True},
                        ],
                        "actions": [
                            {
                                "type": "button",
                                "text": "View on Amazon",
                                "url": data['url']
                            }
                        ]
                    }
                ]
            }

            response = requests.post(
                config.SLACK_WEBHOOK_URL, json=payload, timeout=10)
            response.raise_for_status()

            print("[OK] Slack alert sent")
        except Exception as e:
            print(f"[!] Slack alert failed: {e}")

    @staticmethod
    def send_push(data: Dict, target_price: float = None, stock_alert: bool = False):
        """Send push notification via Pushover"""
        if not config.PUSH_ENABLED:
            return

        try:
            if stock_alert:
                title = "Stock Alert"
                message = f"{data['title'][:100]}\nStock: {data['stock']}"
            else:
                title = "Price Drop Alert"
                message = f"{data['title'][:100]}\nNow: ${data['price']:.2f} (Target: ${target_price:.2f})"

            payload = {
                "token": config.PUSHOVER_API_TOKEN,
                "user": config.PUSHOVER_USER_KEY,
                "title": title,
                "message": message,
                "url": data['url'],
                "url_title": "View on Amazon"
            }

            response = requests.post("https://api.pushover.net/1/messages.json",
                                     data=payload, timeout=10)
            response.raise_for_status()

            print("[OK] Push notification sent")
        except Exception as e:
            print(f"[!] Push notification failed: {e}")

    @classmethod
    def send_all_alerts(cls, data: Dict, target_price: float = None,
                        stock_alert: bool = False, channels: List[str] = None):
        """Send alerts to specified channels"""
        if channels is None:
            channels = ["email"]

        channel_map = {
            "email": cls.send_email,
            "sms": cls.send_sms,
            "telegram": cls.send_telegram,
            "discord": cls.send_discord,
            "slack": cls.send_slack,
            "push": cls.send_push,
        }

        for channel in channels:
            if channel in channel_map:
                channel_map[channel](data, target_price, stock_alert)


# Test the alerts if run directly
if __name__ == "__main__":
    # Example test data
    test_data = {
        "asin": "B08N5WRWNW",
        "title": "Echo Dot (4th Gen) - Test Alert",
        "price": 24.99,
        "price_raw": "$24.99",
        "stock": "In Stock",
        "rating_raw": "4.5 out of 5 stars",
        "reviews_raw": "50,000 ratings",
        "url": "https://www.amazon.com/dp/B08N5WRWNW"
    }

    print("Testing alert system...")
    AlertManager.send_all_alerts(
        test_data, target_price=29.99, channels=["email"])
