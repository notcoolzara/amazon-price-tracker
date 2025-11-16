# scraper/utils.py

import csv
import os
import re
import time
from typing import Optional

from config import CSV_PATH


def ensure_data_dir():
    """Ensure the data directory exists"""
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)


def parse_price_to_float(price_str: Optional[str]) -> Optional[float]:
    """Parse price string to float

    Examples:
        "$24.99" -> 24.99
        "$1,234.56" -> 1234.56
        "24.99" -> 24.99
    """
    if not price_str:
        return None

    # Remove currency symbols and spaces
    cleaned = price_str.replace("$", "").replace(
        "£", "").replace("€", "").strip()

    # Remove commas (for thousands)
    cleaned = cleaned.replace(",", "")

    # Extract first number (handles cases like "$24.99 - $29.99")
    match = re.search(r"(\d+\.?\d*)", cleaned)

    if not match:
        return None

    try:
        return float(match.group(1))
    except (ValueError, AttributeError):
        return None


def save_to_csv(data: dict):
    """Save scraped data to CSV file"""
    ensure_data_dir()
    file_exists = os.path.isfile(CSV_PATH)

    try:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header if file is new
            if not file_exists:
                writer.writerow([
                    "timestamp",
                    "asin",
                    "title",
                    "price_raw",
                    "price",
                    "stock",
                    "rating_raw",
                    "reviews_raw",
                    "url",
                ])

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            writer.writerow([
                timestamp,
                data.get("asin", ""),
                data.get("title", ""),
                data.get("price_raw", ""),
                data.get("price", ""),
                data.get("stock", ""),
                data.get("rating_raw", ""),
                data.get("reviews_raw", ""),
                data.get("url", ""),
            ])

        print(f"[OK] Data saved to CSV")

    except Exception as e:
        print(f"[!] Error saving to CSV: {e}")


def load_from_csv() -> list:
    """Load all data from CSV file"""
    if not os.path.isfile(CSV_PATH):
        return []

    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        print(f"[!] Error loading CSV: {e}")
        return []


# Test the functions
if __name__ == "__main__":
    # Test price parsing
    test_prices = [
        "$24.99",
        "$1,234.56",
        "24.99",
        "$19.99 - $29.99",
        "£15.50",
        "€20.00",
        None,
        "",
        "Invalid"
    ]

    print("Testing price parsing:")
    for price in test_prices:
        result = parse_price_to_float(price)
        print(f"  {price!r:20} -> {result}")
