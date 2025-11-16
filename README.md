# Amazon Price & Stock Tracker  
A professional-grade price and stock tracking tool built with **Python**, **Streamlit**, and a custom **TLS-fingerprinted scraper**. Designed to reliably collect Amazon product data and provide a clean visual dashboard for monitoring changes over time.

This project is ideal for:
- Price monitoring
- Stock alerts
- Competitor tracking
- Portfolio/Upwork scraping showcase
- Automated data collection & visualization

---

## Features

### **Amazon Scraper (TLS-Fingerprint Based)**
- Mimics real browser TLS signatures using `tls-client`
- Supports multi-step warm-up requests to bypass Amazon bot detection
- Randomized header rotation
- Cookie-based session spoofing  
- Multi-path XPath parsing (high accuracy)
- Retrys & exponential backoff for reliability

###  **Streamlit Dashboard**
- Live visualization of tracked product data  
- Line chart of price history  
- Stock availability tracking  
- Rating & review extraction  
- One-click “Run Scrape Now” button  
- Displays most recent product metadata

### **CSV Data Storage**
- Append-based price & stock logging  
- Easy to export to Excel, Power BI, or pandas  
- Auto-creates directories and files if missing  

---

## 🧱 Project Structure
- pip install -r requirements.txt
- python main.py --import-csv products_sample.csv
- streamlit run dashboard/app.py
- python main.py --loop --interval-minutes 30

### **Alert Examples:**

**Price Drop Alert:**
```
🎉 Price Drop Alert!
Echo Dot (4th Gen) is now $25.99 (target: $29.99)
You Save: $4.00
View on Amazon →
```

**Stock Alert:**
```
📦 Stock Alert!
Fire TV Stick 4K is now In Stock!
Current Price: $39.99
View on Amazon →
