# scraper/amazon_scraper.py

import random
import time
import requests
from lxml import html
import tls_client

from config import HEADERS_LIST, BASE_URL, RETRY_COUNT, RETRY_BACKOFF


class AmazonScraper:

    def __init__(self, asin):
        self.asin = asin
        # Use desktop URL instead of mobile
        self.url = f"https://www.amazon.com/dp/{self.asin}"

    def fetch(self):
        # Use different client identifiers randomly
        client_ids = [
            "chrome_120",
            "chrome_119",
            "chrome_118",
            "firefox_120",
            "safari_ios_16_5"
        ]

        client = tls_client.Session(
            client_identifier=random.choice(client_ids),
            random_tls_extension_order=True
        )

        # ---------------------------
        # Multi-step warm-up process
        # ---------------------------
        print("[*] Starting warm-up sequence...")

        try:
            # Step 1: Visit homepage
            warm_headers = {
                "user-agent": random.choice(HEADERS_LIST)["user-agent"],
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.9",
                "accept-encoding": "gzip, deflate, br",
                "connection": "keep-alive",
                "upgrade-insecure-requests": "1",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "cache-control": "max-age=0",
            }

            # Visit homepage
            warm1 = client.get(
                "https://www.amazon.com/",
                headers=warm_headers,
                timeout_seconds=15,
            )
            print(f"   ✓ Homepage visited (Status: {warm1.status_code})")
            time.sleep(random.uniform(2, 4))

            # Step 2: Visit a category page (Books)
            warm2 = client.get(
                "https://www.amazon.com/books-used-books-textbooks/b?node=283155",
                headers=warm_headers,
                timeout_seconds=15,
            )
            print(f"   ✓ Category page visited (Status: {warm2.status_code})")
            time.sleep(random.uniform(2, 4))

            # Extract all cookies
            warm_cookies = warm2.cookies or {}
            print(f"🍪 Cookies collected: {len(warm_cookies)} cookies")

        except Exception as e:
            print(f"⚠️ Warm-up sequence failed: {e}")
            warm_cookies = {}

        # ---------------------------------------------------------

        for attempt in range(1, RETRY_COUNT + 1):
            print(f"\n🔍 Attempt {attempt}/{RETRY_COUNT}")

            # Rotate headers for each attempt
            headers = random.choice(HEADERS_LIST).copy()

            # Add more realistic headers
            headers.update({
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "max-age=0",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "referer": "https://www.amazon.com/",
            })

            # Build realistic cookies from warm-up
            cookies = {c.name: c.value for c in warm_cookies}

            # Add essential cookies if missing
            if not cookies.get("session-id"):
                cookies["session-id"] = f"142-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}"
            if not cookies.get("ubid-main"):
                cookies["ubid-main"] = f"133-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}"

            cookies.update({
                "i18n-prefs": "USD",
                "lc-main": "en_US",
            })

            try:
                # Add random delay before request
                time.sleep(random.uniform(1, 3))

                response = client.get(
                    self.url,
                    headers=headers,
                    cookies=cookies,
                    timeout_seconds=15,
                    allow_redirects=True
                )

                print(f"   Status Code: {response.status_code}")

                # Check response length
                print(f"   Response Length: {len(response.text)} chars")

                text_lower = response.text.lower()

                # Check for blocks (removed false positive patterns)
                blocked_patterns = [
                    "enter the characters you see below",
                    "automated access",
                    "robot check",
                    "sorry, we just need to make sure you're not a robot",
                    "to discuss automated access to amazon data please contact",
                    "api-services-support@amazon.com",
                ]

                blocked = [p for p in blocked_patterns if p in text_lower]

                if blocked:
                    print(f"   ⚠️ Blocked! Detected: {blocked}")

                    # Exponential backoff with jitter
                    wait_time = RETRY_BACKOFF * attempt + random.uniform(1, 3)
                    print(f"   ⏳ Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    continue

                # Check if we got actual product data
                has_product_data = any([
                    "productTitle" in response.text,
                    "acrCustomerReviewText" in response.text,
                    "priceblock_ourprice" in response.text,
                    "a-price-whole" in response.text,
                    '"title":' in response.text[:5000]
                ])

                if has_product_data:
                    print("   ✅ Valid product page received!")
                    return response.text
                else:
                    print("   ⚠️ Page doesn't contain expected product data")
                    print(f"   First 500 chars: {response.text[:500]}")
                    time.sleep(RETRY_BACKOFF * attempt)
                    continue

            except Exception as e:
                print(f"   ❌ Request error: {e}")
                time.sleep(RETRY_BACKOFF * attempt)

        print("\n❌ All attempts failed. Amazon is blocking requests.")
        print("💡 Suggestions:")
        print("   - Wait 10-15 minutes before trying again")
        print("   - Try using a VPN or different network")
        print("   - Consider using a proxy service")
        print("   - Use Amazon's official API for production use")

        return None

    def parse(self, html_source):
        """Parse title, price, stock, rating, and reviews using robust XPaths."""

        tree = html.fromstring(html_source)

        def xp(query):
            result = tree.xpath(query)
            if not result:
                return None
            text = result[0]
            if hasattr(text, 'strip'):
                return text.strip()
            return str(text).strip()

        def xp_all(query):
            """Get all matching results"""
            results = tree.xpath(query)
            return [r.strip() if hasattr(r, 'strip') else str(r).strip() for r in results]

        # Title - multiple attempts
        title = (
            xp('//span[@id="productTitle"]/text()')
            or xp('//h1[@id="title"]//span[@id="productTitle"]/text()')
            or xp('//h1[contains(@class, "product-title")]//text()')
            or xp('//div[@id="titleSection"]//h1//text()')
        )

        # Price - Amazon has many price variations
        price = None

        # Try standard price locations
        price_attempts = [
            '//span[@class="a-price aok-align-center reinventPricePriceToPayMargin priceToPay"]//span[@class="a-offscreen"]/text()',
            '//span[@class="a-price aok-align-center"]//span[@class="a-offscreen"]/text()',
            '//span[contains(@class, "a-price") and contains(@class, "a-text-price")]//span[@class="a-offscreen"]/text()',
            '//span[@id="priceblock_ourprice"]/text()',
            '//span[@id="priceblock_dealprice"]/text()',
            '//span[@id="price_inside_buybox"]/text()',
            '//span[@data-a-color="price"]//span[@class="a-offscreen"]/text()',
            '(//span[contains(@class, "a-price")]//span[@class="a-offscreen"])[1]/text()',
            '//div[@id="corePrice_feature_div"]//span[@class="a-offscreen"]/text()',
            '//div[@id="corePriceDisplay_desktop_feature_div"]//span[@class="a-offscreen"]/text()',
        ]

        for attempt in price_attempts:
            price = xp(attempt)
            if price:
                break

        # If still no price, try to find any price-like text
        if not price:
            all_prices = xp_all('//span[@class="a-offscreen"]/text()')
            for p in all_prices:
                if '$' in p and any(char.isdigit() for char in p):
                    price = p
                    break

        # Stock - multiple patterns
        stock = (
            xp('//div[@id="availability"]//span[@class="a-size-medium a-color-success"]/text()')
            or xp('//div[@id="availability"]//span[@class="a-size-medium a-color-price"]/text()')
            or xp('//div[@id="availability"]//span/text()')
            or xp('//div[@id="availability"]/span/text()')
            or xp('normalize-space(//div[@id="availability"])')
            or xp('//div[@id="availabilityInsideBuyBox_feature_div"]//span/text()')
        )

        if stock:
            stock = " ".join(stock.split())

        # Rating & reviews - try multiple locations
        rating = (
            xp('//span[@data-hook="rating-out-of-text"]/text()')
            or xp('//i[contains(@class, "a-icon-star")]//span[@class="a-icon-alt"]/text()')
            or xp('//span[@id="acrPopover"]/@title')
            or xp('//i[@data-hook="average-star-rating"]//span/text()')
        )

        reviews = (
            xp('//span[@id="acrCustomerReviewText"]/text()')
            or xp('//span[@data-hook="total-review-count"]/text()')
            or xp('//a[@id="acrCustomerReviewLink"]/span/text()')
        )

        # Validate we got real data
        if not title:
            print("⚠️ Parse warning: No title found - might be blocked or wrong page")
            # Try to see if it's a CAPTCHA page
            if "captcha" in html_source.lower() or "robot check" in html_source.lower():
                print("❌ CAPTCHA detected!")
                return None

        result = {
            "asin": self.asin,
            "title": title,
            "price_raw": price,
            "stock": stock or "Unknown",
            "rating_raw": rating,
            "reviews_raw": reviews,
            "url": self.url,
        }

        # Debug output
        print(f"\n📦 Parsed Data:")
        for key, value in result.items():
            if key != 'url':
                display_value = value[:100] + "..." if value and len(str(value)) > 100 else value
                print(f"   {key}: {display_value}")

        return result