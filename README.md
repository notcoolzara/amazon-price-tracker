# Amazon Price & Stock Tracker  
A professional-grade price and stock tracking tool built with **Python**, **Streamlit**, and a custom **TLS-fingerprinted scraper**. Designed to reliably collect Amazon product data and provide a clean visual dashboard for monitoring changes over time.

This project is ideal for:
- Price monitoring
- Stock alerts
- Competitor tracking
- Portfolio/Upwork scraping showcase
- Automated data collection & visualization

---

##Features

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

