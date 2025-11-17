# scraper/amazon_scraper.py

import random
import time
from lxml import html
import tls_client

from config import HEADERS_LIST, BASE_URL, RETRY_COUNT, RETRY_BACKOFF


class AmazonScraper:

    def __init__(self, asin):
        self.asin = asin
        self.url = f"https://www.amazon.com/dp/{self.asin}"

    # ============================================================
    # FETCH PAGE
    # ============================================================

    def fetch(self):
        client_ids = [
            "chrome_120", "chrome_119", "chrome_118",
            "firefox_120", "safari_ios_16_5"
        ]

        client = tls_client.Session(
            client_identifier=random.choice(client_ids),
            random_tls_extension_order=True
        )

        print("[*] Starting warm-up sequence...")

        try:
            warm_headers = {
                "user-agent": random.choice(HEADERS_LIST)["user-agent"],
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.9",
                "accept-encoding": "gzip, deflate, br",
                "connection": "keep-alive",
                "upgrade-insecure-requests": "1",
            }

            warm1 = client.get("https://www.amazon.com/",
                               headers=warm_headers, timeout_seconds=15)
            print(f"   [OK] Homepage visited (Status: {warm1.status_code})")
            time.sleep(random.uniform(2, 4))

            warm2 = client.get("https://www.amazon.com/books-used-books-textbooks/b?node=283155",
                               headers=warm_headers, timeout_seconds=15)
            print(f"   [OK] Category visited (Status: {warm2.status_code})")

            warm_cookies = warm2.cookies
        except Exception as e:
            print(f"[!] Warm-up failed: {e}")
            warm_cookies = {}

        # ============================================================
        # MAIN REQUEST LOOP
        # ============================================================

        for attempt in range(1, RETRY_COUNT + 1):
            print(f"\n[*] Attempt {attempt}/{RETRY_COUNT}")

            headers = random.choice(HEADERS_LIST).copy()
            headers.update({
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.9",
                "upgrade-insecure-requests": "1",
                "referer": "https://www.amazon.com/",
            })

            cookies = {c.name: c.value for c in warm_cookies}
            cookies["i18n-prefs"] = "USD"
            cookies["lc-main"] = "en_US"

            # ensure session cookies exist
            if "session-id" not in cookies:
                cookies["session-id"] = f"142-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}"
            if "ubid-main" not in cookies:
                cookies["ubid-main"] = f"133-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}"

            try:
                time.sleep(random.uniform(1, 3))

                response = client.get(
                    self.url,
                    headers=headers,
                    cookies=cookies,
                    timeout_seconds=15,
                    allow_redirects=True
                )

                print(f"   Status Code: {response.status_code}")

                text_lower = response.text.lower()
                blocked_patterns = [
                    "enter the characters you see below",
                    "automated access",
                    "robot check",
                    "sorry, we just need to make sure you're not a robot",
                    "api-services-support@amazon.com",
                ]

                if any(p in text_lower for p in blocked_patterns):
                    print("   [!] Blocked by Amazon bot check")
                    time.sleep(RETRY_BACKOFF * attempt)
                    continue

                if "productTitle" in response.text or "corePrice" in response.text:
                    print("   [OK] Valid product page received!")
                    return response.text

                print("   [!] Unexpected page content, retrying...")
                time.sleep(RETRY_BACKOFF * attempt)

            except Exception as e:
                print(f"   [X] Request error: {e}")
                time.sleep(RETRY_BACKOFF * attempt)

        print("\n[X] All attempts failed — Amazon is blocking requests.")
        return None

    # ============================================================
    # STRICT BUYBOX PRICE EXTRACTOR
    # ============================================================

    def extract_buybox_price(self, tree):
        """
        Extract the real BuyBox price.
        If multiple prices exist (MSRP + discounted),
        return the lowest price (the true checkout amount).
        """

        xpath_prices = '//div[@id="corePriceDisplay_desktop_feature_div"]//span[@class="a-offscreen"]/text()'
        raw_prices = tree.xpath(xpath_prices)

        clean_prices = []
        for p in raw_prices:
            if "$" in p:
                try:
                    clean_prices.append(float(p.replace("$", "").strip()))
                except:
                    pass

        if clean_prices:
            correct_price = min(clean_prices)
            return f"${correct_price:.2f}"

        return None

    # ============================================================
    # PARSE PAGE
    # ============================================================

    def parse(self, html_source):
        if not html_source:
            print("[X] No HTML received.")
            return None

        tree = html.fromstring(html_source)

        def xp(q):
            r = tree.xpath(q)
            return r[0].strip() if r else None

        def xp_all(q):
            r = tree.xpath(q)
            return [i.strip() for i in r]

        # ============================
        # TITLE
        # ============================

        title = (
            xp('//span[@id="productTitle"]/text()')
            or xp('//h1//span[@id="productTitle"]/text()')
        )

        # ============================
        # PRICE (STRICT BUYBOX)
        # ============================

        price = self.extract_buybox_price(tree)

        if not price:
            BUYBOX_FALLBACK = [
                '//span[@id="price_inside_buybox"]/text()',
                '//span[@id="priceblock_ourprice"]/text()',
                '//span[@id="priceblock_dealprice"]/text()',
                '//span[contains(@class,"priceToPay")]//span[@class="a-offscreen"]/text()'
            ]
            for q in BUYBOX_FALLBACK:
                r = xp(q)
                if r and any(ch.isdigit() for ch in r):
                    price = r
                    break

        # final fallback
        if not price:
            offscreen_prices = xp_all('//span[@class="a-offscreen"]/text()')
            for p in offscreen_prices:
                if "$" in p:
                    price = p
                    break

        # ============================
        # STOCK
        # ============================

        stock = (
            xp('//div[@id="availability"]//span/text()')
            or xp('normalize-space(//div[@id="availability"])')
        )
        if stock:
            stock = " ".join(stock.split())

        # ============================
        # RATING / REVIEWS
        # ============================

        rating = (
            xp('//span[@data-hook="rating-out-of-text"]/text()')
            or xp('//span[@class="a-icon-alt"]/text()')
        )

        reviews = (
            xp('//span[@id="acrCustomerReviewText"]/text()')
            or xp('//span[@data-hook="total-review-count"]/text()')
        )

        # ============================
        # RESULT
        # ============================

        return {
            "asin": self.asin,
            "title": title,
            "price_raw": price,
            "stock": stock or "Unknown",
            "rating_raw": rating,
            "reviews_raw": reviews,
            "url": self.url,
        }
