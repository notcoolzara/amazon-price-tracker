# main.py

import argparse
import time
import sys
import io
import random

import schedule

from scraper.amazon_scraper import AmazonScraper
from scraper.products_manager import ProductsManager
from scraper.utils import save_to_csv, parse_price_to_float
from alerts.unified_alerts import AlertManager

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding='utf-8', errors='replace')


def scrape_all():
    """Scrape all enabled products"""
    print("="*50)
    print("=== Running scrape cycle ===")
    print("="*50)

    manager = ProductsManager()
    products = manager.get_enabled_products()

    if not products:
        print("[!] No products to track. Add products via dashboard.")
        return

    print(f"[*] Tracking {len(products)} products\n")

    for idx, item in enumerate(products, 1):
        asin = item["asin"]
        name = item["name"]
        target_price = item.get("target_price")
        stock_alert = item.get("stock_alert", False)
        alert_channels = item.get("alert_channels", ["email"])

        print(f"\n[{idx}/{len(products)}] Checking {name}")
        print(f"         ASIN: {asin}")

        scraper = AmazonScraper(asin)
        html_source = scraper.fetch()

        if not html_source:
            print("   [X] Failed to fetch page")
            continue

        data = scraper.parse(html_source)

        if not data:
            print("[X] Amazon returned blocked/invalid data. Skipping save.")
            continue

        data["price"] = parse_price_to_float(data.get("price_raw"))

        print(f"   Title : {data.get('title', 'N/A')[:80]}")
        print(f"   Price : {data.get('price')} (raw: {data.get('price_raw')})")
        print(f"   Stock : {data.get('stock')}")

        # Save to CSV
        save_to_csv(data)

        # Update last checked time
        manager.update_product(
            asin, last_checked=time.strftime("%Y-%m-%d %H:%M:%S"))

        # Check for price alert
        if target_price is not None and data.get("price") is not None:
            if data["price"] <= target_price:
                print(
                    f"   [!] PRICE ALERT! Below target (${target_price:.2f})")
                AlertManager.send_all_alerts(
                    data,
                    target_price=target_price,
                    stock_alert=False,
                    channels=alert_channels
                )
            else:
                print(
                    f"   [i] Price ${data['price']:.2f} above target ${target_price:.2f}")

        # Check for stock alert
        if stock_alert and data.get("stock"):
            stock_lower = data["stock"].lower()
            if "in stock" in stock_lower or "available" in stock_lower:
                print(f"   [!] STOCK ALERT! Item is in stock")
                AlertManager.send_all_alerts(
                    data,
                    stock_alert=True,
                    channels=alert_channels
                )

        # Add delay between products to avoid rate limiting
        if idx < len(products):
            delay = random.uniform(5, 10)
            print(f"   [*] Waiting {delay:.1f}s before next product...")
            time.sleep(delay)

    print("\n" + "="*50)
    print("[OK] Scrape cycle completed")
    print("="*50)


def main():
    parser = argparse.ArgumentParser(
        description="Amazon Price & Stock Tracker")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously with schedule instead of a single run.",
    )
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=30,
        help="Interval in minutes for scheduled scraping (used with --loop).",
    )
    parser.add_argument(
        "--import-csv",
        type=str,
        help="Import products from CSV file (columns: asin, name, target_price)",
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        help="Export products to CSV file",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all tracked products",
    )

    args = parser.parse_args()

    manager = ProductsManager()

    # Handle CSV import
    if args.import_csv:
        count = manager.import_from_csv(args.import_csv)
        print(f"[OK] Imported {count} products")
        return

    # Handle CSV export
    if args.export_csv:
        if manager.export_to_csv(args.export_csv):
            print(f"[OK] Exported products to {args.export_csv}")
        return

    # List products
    if args.list:
        products = manager.load_products()
        print(f"\n{'='*80}")
        print(f"Total Products: {len(products)}")
        print(f"{'='*80}")
        for idx, p in enumerate(products, 1):
            status = "[ENABLED]" if p.get("enabled", True) else "[DISABLED]"
            print(f"{idx}. {status} {p['name'][:50]}")
            print(f"   ASIN: {p['asin']}")
            print(f"   Target Price: ${p.get('target_price', 'N/A')}")
            print(f"   Stock Alert: {p.get('stock_alert', False)}")
            print(
                f"   Channels: {', '.join(p.get('alert_channels', ['email']))}")
            print()
        return

    # Run scraper
    if args.loop:
        schedule.every(args.interval_minutes).minutes.do(scrape_all)
        print(
            f"[*] Scheduler started. Interval: {args.interval_minutes} minutes.")
        print("[*] Press Ctrl+C to stop\n")

        # Run immediately on start
        scrape_all()

        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        scrape_all()


if __name__ == "__main__":
    main()
