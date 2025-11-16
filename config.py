# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Base settings
BASE_URL = "https://www.amazon.com/dp/"
RETRY_COUNT = 3
RETRY_BACKOFF = 3

# File paths
CSV_PATH = os.path.join("data", "history.csv")
PRODUCTS_DB_PATH = os.path.join("data", "products.json")

# Rotate between multiple realistic user agents
HEADERS_LIST = [
    {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
    },
    {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ),
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
    },
    {
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
    },
]

# ==============================================
# EMAIL ALERTS
# ==============================================
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# ==============================================
# SMS ALERTS (Twilio)
# ==============================================
SMS_ENABLED = os.getenv("SMS_ENABLED", "false").lower() == "true"
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
RECEIVER_PHONE_NUMBER = os.getenv("RECEIVER_PHONE_NUMBER")

# ==============================================
# TELEGRAM ALERTS
# ==============================================
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==============================================
# DISCORD ALERTS
# ==============================================
DISCORD_ENABLED = os.getenv("DISCORD_ENABLED", "false").lower() == "true"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ==============================================
# SLACK ALERTS
# ==============================================
SLACK_ENABLED = os.getenv("SLACK_ENABLED", "false").lower() == "true"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# ==============================================
# PUSH NOTIFICATIONS (Pushover)
# ==============================================
PUSH_ENABLED = os.getenv("PUSH_ENABLED", "false").lower() == "true"
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
